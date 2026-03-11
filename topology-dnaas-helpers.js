/**
 * topology-dnaas-helpers.js - DNAAS Helper Functions
 * 
 * Contains DNAAS suggestion population and result dismissal
 */

'use strict';

window.DnaasHelpers = {
    _editor: null,
    _dnaasSectionId: null,
    
    _getEditor() {
        return this._editor || window.app;
    },
    
    async _ensureDnaasSection() {
        if (this._dnaasSectionId) return this._dnaasSectionId;
        try {
            const resp = await fetch('/api/sections');
            const data = await resp.json();
            const sections = data.sections || [];
            const existing = sections.find(s => s.name === 'DNAAS');
            if (existing) {
                this._dnaasSectionId = existing.id;
                return existing.id;
            }
            const createResp = await fetch('/api/sections', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'DNAAS', icon: '🔗', color: '#FF5E1F' })
            });
            const result = await createResp.json();
            this._dnaasSectionId = result.section.id;
            return result.section.id;
        } catch (err) {
            console.error('[DNAAS] Failed to ensure section:', err);
            throw err;
        }
    },
    
    populateDnaasSuggestions(editor) {
        this._editor = editor; // Store for internal use
        const suggestionsSection = document.getElementById('dnaas-suggestions-section');
        const suggestionsList = document.getElementById('dnaas-suggestions-list');
        const noTerminationMsg = document.getElementById('dnaas-no-termination-msg');
        
        if (!suggestionsSection || !suggestionsList) return;
        
        // Clear previous suggestions
        suggestionsList.innerHTML = '';
        
        // Find all devices on grid with sshConfig or deviceSerial
        const devicesWithAddr = editor.objects.filter(obj => {
            if (obj.type !== 'device') return false;
            const hasSSH = obj.sshConfig && (obj.sshConfig.host || obj.sshConfig.hostBackup);
            const hasSN = obj.deviceSerial && obj.deviceSerial.trim() !== '';
            return hasSSH || hasSN;
        });
        
        // Filter to only termination devices (exclude DNAAS routers)
        const terminationDevices = devicesWithAddr.filter(device => editor.isTerminationDevice(device));
        const dnaasRouters = devicesWithAddr.filter(device => !editor.isTerminationDevice(device));
        
        if (devicesWithAddr.length === 0) {
            suggestionsSection.style.display = 'none';
            return;
        }
        
        // Show the section
        suggestionsSection.style.display = 'block';
        
        // Show warning if no termination devices but there are DNAAS routers
        if (noTerminationMsg) {
            if (terminationDevices.length === 0 && dnaasRouters.length > 0) {
                noTerminationMsg.style.display = 'block';
            } else {
                noTerminationMsg.style.display = 'none';
            }
        }
        
        // Deduplicate by label (case-insensitive) — same device name = same device
        const seenLabels = new Set();
        const uniqueTerminationDevices = terminationDevices.filter(device => {
            const label = (device.label || device.id || '').trim().toLowerCase();
            if (seenLabels.has(label)) return false;
            seenLabels.add(label);
            return true;
        });
        
        // Update device count badge
        const countEl = document.getElementById('dnaas-suggestions-count');
        if (countEl) countEl.textContent = uniqueTerminationDevices.length;
        
        // Create suggestion buttons only for unique termination devices
        uniqueTerminationDevices.forEach((device) => {
            const hostBackup = device.sshConfig?.hostBackup || '';
            const host = device.sshConfig?.host || '';
            const serial = device.deviceSerial || '';
            const label = device.label || device.id;
            
            let addr = '';
            let displayAddr = '';
            
            if (/^\d+\.\d+\.\d+\.\d+$/.test(hostBackup)) {
                addr = hostBackup;
                displayAddr = hostBackup;
            } else if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) {
                addr = host;
                displayAddr = host;
            } else if (/^[a-z0-9]+$/i.test(serial) && !serial.includes('_') && !serial.includes('-')) {
                addr = serial;
                displayAddr = serial;
            } else {
                addr = host || hostBackup || serial || label;
                displayAddr = addr;
            }
            
            const btn = document.createElement('button');
            btn.style.cssText = `
                display: inline-flex; align-items: center; gap: 5px;
                padding: 5px 10px;
                background: rgba(0,180,216,0.08);
                border: 1px solid rgba(0,180,216,0.18);
                border-radius: 6px;
                color: rgba(255,255,255,0.85);
                cursor: pointer;
                font-size: 11px;
                font-weight: 500;
                transition: all 0.2s ease;
                backdrop-filter: blur(6px);
            `;
            const displayText = addr.length > 20 ? `${addr.substring(0,20)}...` : addr;
            const isIP = /^\d+\.\d+\.\d+\.\d+/.test(addr);
            const iconSvg = isIP
                ? '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="rgba(0,180,216,0.8)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
                : '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="rgba(0,180,216,0.8)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1" fill="rgba(0,180,216,0.8)" stroke="none"/><circle cx="6" cy="18" r="1" fill="rgba(0,180,216,0.8)" stroke="none"/></svg>';
            btn.innerHTML = `${iconSvg}<span>${label}</span><span style="color:rgba(255,255,255,0.4);font-size:10px;font-weight:400;">${displayText}</span>`;
            btn.dataset.fullAddr = addr;
            
            btn.onmouseover = () => {
                btn.style.background = 'rgba(0,180,216,0.22)';
                btn.style.borderColor = 'rgba(0,180,216,0.35)';
                btn.style.color = '#fff';
            };
            btn.onmouseout = () => {
                btn.style.background = 'rgba(0,180,216,0.08)';
                btn.style.borderColor = 'rgba(0,180,216,0.18)';
                btn.style.color = 'rgba(255,255,255,0.85)';
            };
            
            btn.onclick = async (e) => {
                e.stopPropagation();
                
                // Get full address from data attribute or original addr
                let discoveryAddr = btn.dataset.fullAddr || addr;
                
                // Try to look up serial from inventory for better discovery
                    try {
                        const inventory = await ScalerAPI.getDeviceInventory();
                        if (inventory && inventory.devices) {
                            // Normalize for comparison - strip date suffix like "(05-Jan-2026-18:48:06)"
                            const normalizedLabel = (label || '').split('(')[0].trim();
                        const normalizedAddr = (discoveryAddr || '').split('(')[0].trim();
                            
                        // First check if discoveryAddr is already a valid serial in inventory
                        if (inventory.devices[discoveryAddr] || inventory.devices[discoveryAddr.toUpperCase()]) {
                            // Already a valid serial, use it (prefer uppercase version if exists)
                            discoveryAddr = inventory.devices[discoveryAddr.toUpperCase()] ? discoveryAddr.toUpperCase() : discoveryAddr;
                            console.log(`[DNAAS] Using serial directly: ${discoveryAddr}`);
                        } else {
                            // Try to find by hostname
                            for (const [invSerial, info] of Object.entries(inventory.devices)) {
                                const invHostname = (info.hostname || '').split('(')[0].trim();
                                // Compare normalized versions and also check full hostname match
                                if (invHostname === normalizedLabel || 
                                    invHostname === normalizedAddr ||
                                    info.hostname === discoveryAddr ||
                                    info.hostname === label ||
                                    invHostname.includes(normalizedLabel) ||
                                    normalizedLabel.includes(invHostname)) {
                                    discoveryAddr = invSerial;
                                    console.log(`[DNAAS] Resolved ${label} → ${invSerial}`);
                                    break;
                                }
                                }
                            }
                        }
                    } catch (e) {
                    console.warn('[DNAAS] Inventory lookup failed, using original address:', e);
                }
                
                // Fill the input with the resolved address (user must click Start)
                const serialInput = document.getElementById('dnaas-serial-input');
                if (serialInput) {
                    serialInput.value = discoveryAddr;
                    console.log(`[DNAAS] Set input to: ${discoveryAddr}`);
                    // Focus the start button to indicate user should click it
                    const startBtn = document.getElementById('dnaas-start-discovery');
                    if (startBtn) {
                        startBtn.focus();
                    }
                }
                // DO NOT auto-start - user must click Start button
                editor.showToast(`Device selected: ${discoveryAddr} - click Start to begin`, 'info');
            };
            
            suggestionsList.appendChild(btn);
        });
    },
    
    // Start DNAAS discovery from the panel's Quick Discovery input
    async startDnaasDiscovery(serial) {
        
        // Get UI elements
        const dnaasBtn = document.getElementById('btn-dnaas');
        const progressSection = document.getElementById('dnaas-progress-section');
        const progressText = document.getElementById('dnaas-progress-text');
        const progressBar = document.getElementById('dnaas-progress-bar');
        const progressSpinner = document.getElementById('dnaas-spinner');
        const outputDiv = document.getElementById('dnaas-output');
        const statusSpan = document.getElementById('dnaas-panel-status');
        const startBtn = document.getElementById('dnaas-start-discovery');
        const resultActions = document.getElementById('dnaas-result-actions');
        const cancelBtn = document.getElementById('dnaas-cancel-discovery');
        
        // Reset cancellation state
        editor._discoveryAbortController = new AbortController();
        editor._currentDiscoveryJobId = null;
        
        // === LOADING STATE: Purple button + spinning icon ===
        if (dnaasBtn) {
            dnaasBtn.classList.remove('dnaas-complete', 'dnaas-error');
            dnaasBtn.classList.add('dnaas-loading');
        }
        
        // Show progress section
        if (progressSection) progressSection.style.display = 'block';
        if (progressText) progressText.textContent = 'Starting discovery...';
        if (progressBar) progressBar.style.width = '5%';
        // Reset spinner to spinning state
        if (progressSpinner) {
            progressSpinner.innerHTML = '';
            progressSpinner.style.animation = 'spin 1s linear infinite';
            progressSpinner.style.border = '2px solid #9b59b6';
            progressSpinner.style.borderTopColor = 'transparent';
        }
        if (outputDiv) outputDiv.textContent = `Connecting to ${serial}...\n`;
        if (statusSpan) {
            statusSpan.textContent = '⏳ Running';
            statusSpan.style.background = 'rgba(155, 89, 182, 0.5)';
        }
        if (startBtn) startBtn.disabled = true;
        if (resultActions) resultActions.style.display = 'none';
        if (cancelBtn) cancelBtn.style.display = 'block';
        
        let jobId = null;
        let resultFile = null;
        
        try {
            // Check if ScalerAPI is available
            if (typeof ScalerAPI !== 'undefined' && ScalerAPI.startDnaasDiscovery) {
                
                // Start discovery via API
                if (outputDiv) outputDiv.textContent += `Calling DNAAS API...\n`;
                if (progressBar) progressBar.style.width = '10%';
                
                let startResult;
                try {
                    startResult = await ScalerAPI.startDnaasDiscovery({ serial1: serial });
                } catch (apiErr) {
                    throw apiErr; // Re-throw to be caught by outer catch
                }
                jobId = startResult.job_id;
                editor._currentDiscoveryJobId = jobId;
                
                if (outputDiv) outputDiv.textContent += `Job started: ${jobId}\n`;
                if (progressBar) progressBar.style.width = '15%';
                
                // Poll for status (10 minutes timeout for large BD discovery)
                let attempts = 0;
                const maxAttempts = 600; // 10 minutes max - BD discovery can take a while
                
                while (attempts < maxAttempts) {
                    // Check if cancelled
                    if (editor._discoveryAbortController?.signal.aborted) {
                        throw new Error('Discovery cancelled by user');
                    }
                    
                    await new Promise(r => setTimeout(r, 1000)); // Wait 1 second
                    attempts++;
                    
                    try {
                        const status = await ScalerAPI.getDnaasStatus(jobId);
                        
                        // Update progress with time info
                        const progress = status.progress || Math.min((attempts / maxAttempts) * 100, 95);
                        const elapsed = Math.floor(attempts / 60);
                        const remaining = Math.floor((maxAttempts - attempts) / 60);
                        if (progressBar) progressBar.style.width = `${Math.min(95, 15 + progress * 0.8)}%`;
                        if (progressText) {
                            const statusMsg = status.status || 'Running...';
                            progressText.textContent = `${statusMsg} (${elapsed}m elapsed, ~${remaining}m remaining)`;
                        }
                        
                        // Append output lines
                        if (status.output && outputDiv) {
                            outputDiv.textContent = status.output;
                            outputDiv.scrollTop = outputDiv.scrollHeight;
                        }
                        
                        // Check if complete
                        if (status.status === 'completed' || status.status === 'success') {
                            resultFile = status.result_file;
                            break;
                        } else if (status.status === 'failed' || status.status === 'error') {
                            throw new Error(status.error || 'Discovery failed');
                        }
                    } catch (pollErr) {
                        // Check if this is a discovery failure or a transient error
                        if (pollErr.message.includes('not found')) {
                            // Job not ready yet, wait and retry
                            await new Promise(r => setTimeout(r, 500));
                        } else if (pollErr.message.includes('Connection failed') || 
                                   pollErr.message.includes('Discovery failed') ||
                                   pollErr.message.includes('No devices')) {
                            // Actual discovery failure - propagate the error
                            throw pollErr;
                        }
                        // Other transient errors - continue polling
                    }
                }
                
                if (!resultFile && attempts >= maxAttempts) {
                    throw new Error('Discovery timed out');
                }
                
            } else {
                // Fallback: Direct API call without ScalerAPI
                
                if (outputDiv) outputDiv.textContent += `Calling discovery API...\n`;
                
                const response = await fetch('/api/dnaas/discovery/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ serial1: serial })
                });
                
                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.detail || `API error: ${response.status}`);
                }
                
                const startResult = await response.json();
                jobId = startResult.job_id;
                editor._currentDiscoveryJobId = jobId;
                
                if (outputDiv) outputDiv.textContent += `Job started: ${jobId}\n`;
                if (progressBar) progressBar.style.width = '20%';
                
                // Poll for status (10 minutes timeout for large BD discovery)
                let attempts = 0;
                const maxAttempts = 600; // 10 minutes max - BD discovery can take a while
                
                while (attempts < maxAttempts) {
                    // Check if cancelled
                    if (editor._discoveryAbortController?.signal.aborted) {
                        throw new Error('Discovery cancelled by user');
                    }
                    
                    await new Promise(r => setTimeout(r, 1000));
                    attempts++;
                    
                    const statusResp = await fetch(`/api/dnaas/discovery/status?job_id=${encodeURIComponent(jobId)}`);
                    if (statusResp.ok) {
                        const status = await statusResp.json();
                        
                        // Update progress with time info
                        const progress = status.progress || Math.min((attempts / maxAttempts) * 100, 95);
                        const elapsed = Math.floor(attempts / 60);
                        const remaining = Math.floor((maxAttempts - attempts) / 60);
                        if (progressBar) progressBar.style.width = `${Math.min(95, 20 + progress * 0.75)}%`;
                        if (progressText) {
                            const statusMsg = status.status || 'Running...';
                            progressText.textContent = `${statusMsg} (${elapsed}m elapsed, ~${remaining}m remaining)`;
                        }
                        
                        if (status.output && outputDiv) {
                            outputDiv.textContent = status.output;
                            outputDiv.scrollTop = outputDiv.scrollHeight;
                        }
                        
                        if (status.status === 'completed' || status.status === 'success') {
                            resultFile = status.result_file;
                            break;
                        } else if (status.status === 'failed' || status.status === 'error') {
                            throw new Error(status.error || 'Discovery failed');
                        }
                    }
                }
                
                if (!resultFile && attempts >= maxAttempts) {
                    throw new Error('Discovery timed out');
                }
            }
            
            // === SUCCESS STATE: Green button ===
            if (dnaasBtn) {
                dnaasBtn.classList.remove('dnaas-loading', 'dnaas-panel-open', 'dnaas-error');
                dnaasBtn.classList.add('dnaas-complete');
                console.log('[DNAAS] Success state applied to button:', dnaasBtn.className);
            }
            if (progressBar) progressBar.style.width = '100%';
            if (progressText) progressText.textContent = 'Discovery complete!';
            // Stop spinner and show checkmark
            if (progressSpinner) {
                progressSpinner.style.animation = 'none';
                progressSpinner.style.border = '2px solid #27ae60';
                progressSpinner.innerHTML = '✓';
                progressSpinner.style.display = 'flex';
                progressSpinner.style.alignItems = 'center';
                progressSpinner.style.justifyContent = 'center';
                progressSpinner.style.color = '#27ae60';
                progressSpinner.style.fontSize = '10px';
                progressSpinner.style.fontWeight = 'bold';
            }
            if (statusSpan) {
                statusSpan.textContent = '✓ Complete';
                statusSpan.style.background = 'rgba(39, 174, 96, 0.7)';
            }
            if (outputDiv) outputDiv.textContent += `\n✓ Discovery complete!\nResult: ${resultFile}\n`;
            
            // Show result actions
            if (resultActions) {
                resultActions.style.display = 'flex';
                const loadBtn = document.getElementById('dnaas-load-result');
                if (loadBtn) {
                    loadBtn.onclick = async () => {
                        try {
                            const filename = resultFile.split('/').pop();
                            let data;
                            if (typeof ScalerAPI !== 'undefined') {
                                data = await ScalerAPI.getDnaasFile(filename);
                            } else {
                                const resp = await fetch(`/api/dnaas/discovery/file/${encodeURIComponent(filename)}`);
                                data = await resp.json();
                            }
                            
                            // Enrich termination devices with managed device SSH config
                            data = await editor.enrichTerminationDevicesWithManagedConfig(data);
                            
                            editor.loadDnaasData(data);
                            editor.showToast('Topology loaded from DNAAS discovery!', 'success');
                            
                            // Reset button state after topology is loaded
                            if (dnaasBtn) dnaasBtn.classList.remove('dnaas-complete');
                            
                            // Close the DNAAS panel after loading
                            const dnaasPanel = document.getElementById('dnaas-panel');
                            if (dnaasPanel) dnaasPanel.style.display = 'none';
                        } catch (err) {
                            editor.showToast(`Failed to load: ${err.message}`, 'error');
                        }
                    };
                }
            }
            
            editor.showToast('DNAAS discovery complete!', 'success');
            
            // NOTE: Button stays green (dnaas-complete) until user loads topology or cancels
            // No auto-reset timer - user must take action
            
        } catch (error) {
            
            // === ERROR STATE: Red button ===
            if (dnaasBtn) {
                dnaasBtn.classList.remove('dnaas-loading', 'dnaas-panel-open', 'dnaas-complete');
                dnaasBtn.classList.add('dnaas-error');
                console.log('[DNAAS] Error state applied to button:', dnaasBtn.className);
            }
            if (progressText) progressText.textContent = 'Discovery failed';
            // Stop spinner and show error X
            if (progressSpinner) {
                progressSpinner.style.animation = 'none';
                progressSpinner.style.border = '2px solid #e74c3c';
                progressSpinner.innerHTML = '✗';
                progressSpinner.style.display = 'flex';
                progressSpinner.style.alignItems = 'center';
                progressSpinner.style.justifyContent = 'center';
                progressSpinner.style.color = '#e74c3c';
                progressSpinner.style.fontSize = '10px';
                progressSpinner.style.fontWeight = 'bold';
            }
            if (statusSpan) {
                statusSpan.textContent = '✗ Error';
                statusSpan.style.background = 'rgba(231, 76, 60, 0.7)';
            }
            let userMsg = error.message || 'Unknown error';
            if (userMsg.includes('unreachable') || userMsg.includes('discovery_api')) {
                userMsg = 'API down - check serve.py and discovery_api.py are running';
            } else if (userMsg.includes('Connection failed') || userMsg.includes('SSH') || userMsg.includes('connect')) {
                userMsg = 'SSH connection failed - check device reachability and credentials';
            } else if (userMsg.includes('timeout') || userMsg.includes('MCP') || userMsg.includes('timed out')) {
                userMsg = 'Request timed out - MCP or SSH may be slow';
            }
            if (outputDiv) outputDiv.textContent += `\n[ERROR] ${userMsg}\n`;
            editor.showToast(`Discovery failed: ${userMsg}`, 'error');
            
            // Reset button after 5 seconds
            setTimeout(() => {
                if (dnaasBtn) dnaasBtn.classList.remove('dnaas-error');
            }, 5000);
        } finally {
            if (startBtn) startBtn.disabled = false;
            if (cancelBtn) cancelBtn.style.display = 'none';
            editor._currentDiscoveryJobId = null;
            editor._discoveryAbortController = null;
        }
        
        if (editor.debugger) {
            editor.debugger.logInfo(`DNAAS discovery completed for: ${serial}`);
        }
    },
    
    /**
     * Cancel the current DNAAS topology discovery
     */
    async cancelDnaasDiscovery() {
        const editor = this._getEditor();
        if (!editor._discoveryAbortController) {
            editor.showToast('No discovery in progress', 'info');
            return;
        }
        
        // Signal abortion to the polling loop
        editor._discoveryAbortController.abort();
        
        // Try to cancel the backend job as well
        const jobId = editor._currentDiscoveryJobId;
        if (jobId) {
            try {
                // Determine the right cancel endpoint based on job type
                const isMultiBD = jobId.startsWith('multibd_');
                const cancelEndpoint = isMultiBD 
                    ? '/api/dnaas/multi-bd/cancel' 
                    : '/api/dnaas/discovery/cancel';
                
                if (typeof ScalerAPI !== 'undefined' && ScalerAPI.cancelDnaasDiscovery) {
                    await ScalerAPI.cancelDnaasDiscovery(jobId);
                } else {
                    // Fallback: direct API call to appropriate endpoint
                    await fetch(cancelEndpoint, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ job_id: jobId })
                    });
                }
                console.log(`[DNAAS] Cancelled job ${jobId} via ${cancelEndpoint}`);
            } catch (err) {
                console.warn('[DNAAS] Failed to cancel backend job:', err);
            }
        }
        
        // Update UI immediately
        const dnaasBtn = document.getElementById('btn-dnaas');
        const progressText = document.getElementById('dnaas-progress-text');
        const progressSpinner = document.getElementById('dnaas-spinner');
        const statusSpan = document.getElementById('dnaas-panel-status');
        const cancelBtn = document.getElementById('dnaas-cancel-discovery');
        const outputDiv = document.getElementById('dnaas-output');
        const startBtn = document.getElementById('dnaas-start-discovery');
        
        if (dnaasBtn) {
            dnaasBtn.classList.remove('dnaas-loading', 'dnaas-panel-open', 'dnaas-complete');
            dnaasBtn.classList.add('dnaas-error');
        }
        if (progressText) progressText.textContent = 'Discovery cancelled';
        if (progressSpinner) {
            progressSpinner.style.animation = 'none';
            progressSpinner.style.border = '2px solid #FF7A33';
            progressSpinner.innerHTML = '⚠';
            progressSpinner.style.display = 'flex';
            progressSpinner.style.alignItems = 'center';
            progressSpinner.style.justifyContent = 'center';
            progressSpinner.style.color = '#FF7A33';
            progressSpinner.style.fontSize = '10px';
        }
        if (statusSpan) {
            statusSpan.textContent = '⚠ Cancelled';
            statusSpan.style.background = 'rgba(255, 94, 31, 0.7)';
        }
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (startBtn) startBtn.disabled = false;
        if (outputDiv) outputDiv.textContent += '\n⚠ Discovery cancelled by user\n';
        
        // Clean up tracking state
        editor._currentDiscoveryJobId = null;
        editor._discoveryAbortController = null;
        
        editor.showToast('Discovery cancelled', 'warning');
        
        // Reset button state after 3 seconds
        setTimeout(() => {
            if (dnaasBtn) dnaasBtn.classList.remove('dnaas-error');
        }, 3000);
        
        if (editor.debugger) {
            editor.debugger.logInfo('DNAAS discovery cancelled by user');
        }
    },
    
    /**
     * Start Multi-BD Discovery - discovers ALL Bridge Domains from a device
     * and creates a topology with color-coded links for each BD
     */
    async startMultiBDDiscovery(serialOrHostname) {
        const editor = this._getEditor();
        const dnaasBtn = document.getElementById('btn-dnaas');
        const progressSection = document.getElementById('dnaas-progress-section');
        const progressText = document.getElementById('dnaas-progress-text');
        const progressBar = document.getElementById('dnaas-progress-bar');
        const progressSpinner = document.getElementById('dnaas-spinner');
        const outputDiv = document.getElementById('dnaas-output');
        const statusSpan = document.getElementById('dnaas-panel-status');
        const startBtn = document.getElementById('dnaas-start-discovery');
        const multiBdBtn = document.getElementById('dnaas-multi-bd-discovery');
        const resultActions = document.getElementById('dnaas-result-actions');
        
        // Try to resolve hostname to serial by looking up device on canvas or inventory
        let serial = serialOrHostname;
        
        // First try canvas lookup
        const device = editor.objects.find(obj => 
            obj.type === 'device' && 
            (obj.label === serialOrHostname || 
             obj.sshConfig?.host === serialOrHostname ||
             obj.deviceAddress === serialOrHostname)
        );
        
        if (device) {
            // Try to get serial from device's sshConfig or label
            // Look for a serial-like pattern (lowercase alphanumeric like wk31d7vv00023)
            const possibleSerial = device.sshConfig?.host || device.deviceAddress || device.label;
            
            // If input looks like a hostname (contains _ or uppercase), try to find serial
            if (/[_A-Z]/.test(serialOrHostname) && possibleSerial) {
                // Check if the device has an IP we can use
                const deviceIp = device.sshConfig?.hostBackup || device.sshConfig?.host;
                if (deviceIp && /^\d+\.\d+\.\d+\.\d+$/.test(deviceIp)) {
                    serial = deviceIp;
                    console.log(`[Multi-BD] Using device IP ${deviceIp} for ${serialOrHostname}`);
                }
            }
        }
        
        // If still looks like a hostname (not an IP or serial), try inventory lookup
        if (/[_A-Z\-]/.test(serial) && !/^\d+\.\d+\.\d+\.\d+$/.test(serial)) {
            try {
                const inventory = await ScalerAPI.getDeviceInventory();
                if (inventory && inventory.devices) {
                    // Normalize for comparison - strip date suffix like "(05-Jan-2026-18:48:06)"
                    const normalizedInput = (serialOrHostname || '').split('(')[0].trim();
                    
                    for (const [invSerial, info] of Object.entries(inventory.devices)) {
                        const invHostname = (info.hostname || '').split('(')[0].trim();
                        // Check both normalized and full hostname matches
                        if (invHostname === normalizedInput || 
                            info.hostname === serialOrHostname) {
                            serial = invSerial;
                            console.log(`[Multi-BD] Resolved ${serialOrHostname} → ${invSerial} via inventory`);
                            break;
                        }
                    }
                }
            } catch (e) {
                console.warn('[Multi-BD] Inventory lookup failed:', e);
            }
        }
        
        // Reset cancellation state
        editor._discoveryAbortController = new AbortController();
        editor._currentDiscoveryJobId = null;
        
        // === LOADING STATE ===
        if (dnaasBtn) {
            dnaasBtn.classList.remove('dnaas-complete', 'dnaas-error');
            dnaasBtn.classList.add('dnaas-loading');
        }
        
        // Show progress section
        if (progressSection) progressSection.style.display = 'block';
        if (progressText) progressText.textContent = 'Starting Multi-BD discovery...';
        if (progressBar) progressBar.style.width = '5%';
        if (progressSpinner) {
            progressSpinner.innerHTML = '';
            progressSpinner.style.animation = 'spin 1s linear infinite';
            progressSpinner.style.border = '2px solid #FF5E1F';
            progressSpinner.style.borderTopColor = 'transparent';
        }
        if (outputDiv) outputDiv.textContent = `🌈 Multi-BD Discovery for ${serial}...\n`;
        if (statusSpan) {
            statusSpan.textContent = '⏳ Mapping BDs';
            statusSpan.style.background = 'rgba(255, 94, 31, 0.5)';
        }
        if (startBtn) startBtn.disabled = true;
        if (multiBdBtn) multiBdBtn.disabled = true;
        if (resultActions) resultActions.style.display = 'none';
        
        let resultFile = null;
        
        try {
            // Check if ScalerAPI is available
            if (typeof ScalerAPI !== 'undefined' && ScalerAPI.startMultiBDDiscovery) {
                
                if (outputDiv) outputDiv.textContent += `Calling Multi-BD Discovery API...\n`;
                if (progressBar) progressBar.style.width = '10%';
                
                let startResult;
                try {
                    startResult = await ScalerAPI.startMultiBDDiscovery({ serial: serial });
                } catch (apiErr) {
                    throw apiErr;
                }
                
                const jobId = startResult.job_id;
                editor._currentDiscoveryJobId = jobId;
                
                if (outputDiv) outputDiv.textContent += `Job started: ${jobId}\n`;
                if (progressBar) progressBar.style.width = '15%';
                
                // Poll for status
                let attempts = 0;
                const maxAttempts = 600; // 10 minutes max for multi-BD (large topologies need more time)
                
                while (attempts < maxAttempts) {
                    if (editor._discoveryAbortController?.signal.aborted) {
                        throw new Error('Discovery cancelled');
                    }
                    
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    attempts++;
                    
                    let status;
                    try {
                        status = await ScalerAPI.getMultiBDDiscoveryStatus(jobId);
                    } catch (statusErr) {
                        // If job not found, the server was likely restarted - abort polling
                        if (statusErr.message && statusErr.message.includes('not found')) {
                            throw new Error('Discovery job lost - server may have restarted. Please try again.');
                        }
                        continue;
                    }
                    
                    // Update progress
                    const progress = Math.min(90, 15 + (attempts / maxAttempts) * 75);
                    if (progressBar) progressBar.style.width = `${progress}%`;
                    
                    // Update output with status message
                    if (status.message && outputDiv) {
                        const lines = outputDiv.textContent.split('\n');
                        const lastLine = lines[lines.length - 1] || '';
                        if (!lastLine.includes(status.message)) {
                            outputDiv.textContent += `${status.message}\n`;
                            outputDiv.scrollTop = outputDiv.scrollHeight;
                        }
                    }
                    
                    if (status.status === 'completed') {
                        resultFile = status.result_file;
                        if (progressText) progressText.textContent = `Found ${status.bd_count || '?'} Bridge Domains!`;
                        break;
                    } else if (status.status === 'failed' || status.status === 'error') {
                        // Check if failure is due to no LLDP neighbors
                        const outputText = status.output_lines?.join('\n') || status.error || '';
                        const noLldpDetected = outputText.includes('0 LLDP neighbors') || 
                                               outputText.includes('No LLDP neighbors') ||
                                               outputText.includes('no DNAAS neighbors') ||
                                               outputText.includes('0 DNAAS neighbors') ||
                                               outputText.includes('No Bridge Domains discovered') ||
                                               outputText.includes('cannot discover DNAAS fabric') ||
                                               outputText.includes('LLDP must be enabled');
                        
                        if (noLldpDetected) {
                            // Show special dialog for LLDP issue - seamless integration
                            await editor._showNoLldpDialog(serial, outputDiv, progressSection);
                            return; // Don't throw error, dialog handles the flow
                        }
                        
                        throw new Error(status.error || 'Discovery failed');
                    }
                }
                
                if (!resultFile && attempts >= maxAttempts) {
                    throw new Error('Discovery timed out');
                }
                
            } else {
                // Fallback: Direct API call
                if (outputDiv) outputDiv.textContent += `Using direct API...\n`;
                
                const response = await fetch('/api/dnaas/multi-bd/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ serial: serial })
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'API error');
                }
                
                const result = await response.json();
                resultFile = result.result_file;
                
                if (outputDiv) {
                    outputDiv.textContent += `Found ${result.bd_count || '?'} Bridge Domains\n`;
                }
            }
            
            // === SUCCESS STATE ===
            if (dnaasBtn) {
                dnaasBtn.classList.remove('dnaas-loading', 'dnaas-panel-open', 'dnaas-error');
                dnaasBtn.classList.add('dnaas-complete');
            }
            if (progressBar) progressBar.style.width = '100%';
            if (progressText) progressText.textContent = 'Multi-BD discovery complete!';
            if (progressSpinner) {
                progressSpinner.style.animation = 'none';
                progressSpinner.style.border = '2px solid #27ae60';
                progressSpinner.innerHTML = '✓';
                progressSpinner.style.display = 'flex';
                progressSpinner.style.alignItems = 'center';
                progressSpinner.style.justifyContent = 'center';
                progressSpinner.style.color = '#27ae60';
                progressSpinner.style.fontSize = '10px';
                progressSpinner.style.fontWeight = 'bold';
            }
            if (statusSpan) {
                statusSpan.textContent = '✓ Complete';
                statusSpan.style.background = 'rgba(39, 174, 96, 0.7)';
            }
            if (outputDiv) outputDiv.textContent += `\n✓ Multi-BD Discovery complete!\nResult: ${resultFile}\n`;
            
            // Show result actions
            if (resultActions) {
                resultActions.style.display = 'flex';
                
                const _fetchDiscoveryData = async () => {
                    const filename = resultFile.split('/').pop();
                    let data;
                    if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getMultiBDFile) {
                        data = await ScalerAPI.getMultiBDFile(filename);
                    } else {
                        const resp = await fetch(`/api/dnaas/multi-bd/file/${encodeURIComponent(filename)}`);
                        data = await resp.json();
                    }
                    return await editor.enrichTerminationDevicesWithManagedConfig(data);
                };
                
                const loadBtn = document.getElementById('dnaas-load-result');
                if (loadBtn) {
                    loadBtn.onclick = async () => {
                        try {
                            const data = await _fetchDiscoveryData();
                            
                            window._dnaasDiscoveryData = data;
                            console.log('[Multi-BD] Discovery data cached for Link Table auto-fill:', 
                                        data.metadata?.bridge_domains?.length || 0, 'BDs',
                                        Object.keys(data.metadata?.device_bd_mapping || {}).length, 'devices');
                            
                            editor.loadDnaasData(data);
                            editor.showToast(`Multi-BD topology loaded with ${data.metadata?.bridge_domains?.length || '?'} Bridge Domains!`, 'success');
                            
                            if (dnaasBtn) dnaasBtn.classList.remove('dnaas-complete');
                            const dnaasPanel = document.getElementById('dnaas-panel');
                            if (dnaasPanel) dnaasPanel.style.display = 'none';
                            
                        } catch (loadErr) {
                            console.error('[Multi-BD] Failed to load topology:', loadErr);
                            editor.showToast(`Failed to load topology: ${loadErr.message}`, 'error');
                        }
                    };
                }
                
                const saveBtn = document.getElementById('dnaas-save-as-dnaas');
                if (saveBtn) {
                    saveBtn.onclick = async () => {
                        try {
                            const data = await _fetchDiscoveryData();
                            window._dnaasDiscoveryData = data;
                            editor.loadDnaasData(data);
                            
                            if (dnaasBtn) dnaasBtn.classList.remove('dnaas-complete');
                            const dnaasPanel = document.getElementById('dnaas-panel');
                            if (dnaasPanel) dnaasPanel.style.display = 'none';
                            
                            setTimeout(() => editor.saveAsDnaasTopology(), 300);
                        } catch (saveErr) {
                            console.error('[Multi-BD] Failed to save topology:', saveErr);
                            editor.showToast(`Failed to save: ${saveErr.message}`, 'error');
                        }
                    };
                }
            }
            
        } catch (error) {
            console.error('[Multi-BD] Discovery error:', error);
            
            // === ERROR STATE ===
            if (dnaasBtn) {
                dnaasBtn.classList.remove('dnaas-loading', 'dnaas-panel-open', 'dnaas-complete');
                dnaasBtn.classList.add('dnaas-error');
            }
            if (progressText) progressText.textContent = 'Multi-BD discovery failed';
            if (progressSpinner) {
                progressSpinner.style.animation = 'none';
                progressSpinner.style.border = '2px solid #e74c3c';
                progressSpinner.innerHTML = '✗';
                progressSpinner.style.display = 'flex';
                progressSpinner.style.alignItems = 'center';
                progressSpinner.style.justifyContent = 'center';
                progressSpinner.style.color = '#e74c3c';
                progressSpinner.style.fontSize = '10px';
                progressSpinner.style.fontWeight = 'bold';
            }
            if (statusSpan) {
                statusSpan.textContent = '✗ Error';
                statusSpan.style.background = 'rgba(231, 76, 60, 0.7)';
            }
            if (outputDiv) outputDiv.textContent += `\n✗ Error: ${error.message}\n`;
            
            editor.showToast(`Multi-BD discovery failed: ${error.message}`, 'error');
            
            setTimeout(() => {
                if (dnaasBtn) dnaasBtn.classList.remove('dnaas-error');
            }, 5000);
            
        } finally {
            if (startBtn) startBtn.disabled = false;
            if (multiBdBtn) multiBdBtn.disabled = false;
            editor._currentDiscoveryJobId = null;
            editor._discoveryAbortController = null;
        }
        
        if (editor.debugger) {
            editor.debugger.logInfo(`Multi-BD discovery completed for: ${serial}`);
        }
    },
    
    /**
     * Dismiss the DNAAS discovery result without loading the topology.
     * Resets the button state and closes the panel.
     */
    dismissDnaasResult(editor) {
        // Reset button state
        const dnaasBtn = document.getElementById('btn-dnaas');
        if (dnaasBtn) {
            dnaasBtn.classList.remove('dnaas-complete', 'dnaas-loading', 'dnaas-error');
        }
        
        // Hide the result actions
        const resultActions = document.getElementById('dnaas-result-actions');
        if (resultActions) resultActions.style.display = 'none';
        
        // Reset progress section
        const progressSection = document.getElementById('dnaas-progress-section');
        if (progressSection) progressSection.style.display = 'none';
        
        // Reset status
        const statusSpan = document.getElementById('dnaas-panel-status');
        if (statusSpan) {
            statusSpan.textContent = 'Ready';
            statusSpan.style.background = 'rgba(255,255,255,0.2)';
        }
        
        // Close the panel
        const dnaasPanel = document.getElementById('dnaas-panel');
        if (dnaasPanel) dnaasPanel.style.display = 'none';
        
        editor.showToast('Discovery result dismissed', 'info');
        
        if (editor.debugger) {
            editor.debugger.logInfo('DNAAS discovery result dismissed');
        }
    },
    
    /**
     * Show dialog when discovery fails due to no LLDP neighbors.
     * Offers to enable LLDP and admin-state on all interfaces.
     */
    async _showNoLldpDialog(serial, outputDiv, progressSection) {
        // Update the output to show the issue
        if (outputDiv) {
            outputDiv.innerHTML = `
<span style="color: #e74c3c;">⚠ No LLDP Neighbors Found</span>

The device <span style="color: #FF7A33;">${serial}</span> has no LLDP neighbors.
This means it's not connected to DNAAS fabric infrastructure.

<span style="color: #3498db;">Possible causes:</span>
  • Interfaces to DNAAS fabric are admin-down
  • LLDP is not enabled on fabric-facing interfaces
  • Physical links are disconnected

<span style="color: #27ae60;">Would you like to auto-configure?</span>
This will enable LLDP and admin-state on all interfaces
to help discover DNAAS neighbors.
            `;
        }
        
        // Update progress text
        const progressText = document.getElementById('dnaas-progress-text');
        if (progressText) {
            progressText.innerHTML = '<span style="color: #FF7A33;">⚠ No LLDP Neighbors</span>';
        }
        
        // Hide the spinner and show action buttons
        const progressSpinner = document.getElementById('dnaas-spinner');
        if (progressSpinner) {
            progressSpinner.style.display = 'none';
        }
        
        // Create action buttons container
        const actionContainer = document.createElement('div');
        actionContainer.id = 'lldp-action-container';
        actionContainer.style.cssText = `
            display: flex;
            gap: 10px;
            margin-top: 15px;
            justify-content: center;
        `;
        
        // Enable LLDP button
        const enableBtn = document.createElement('button');
        enableBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            Enable LLDP on All Interfaces
        `;
        enableBtn.style.cssText = `
            padding: 10px 16px;
            background: linear-gradient(135deg, #27ae60, #219a52);
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-weight: 600;
            font-size: 12px;
            display: flex;
            align-items: center;
            transition: all 0.2s ease;
        `;
        enableBtn.onmouseover = () => enableBtn.style.filter = 'brightness(1.1)';
        enableBtn.onmouseout = () => enableBtn.style.filter = 'brightness(1)';
        
        // Cancel button
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancel';
        cancelBtn.style.cssText = `
            padding: 10px 16px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 6px;
            color: #bdc3c7;
            cursor: pointer;
            font-weight: 500;
            font-size: 12px;
            transition: all 0.2s ease;
        `;
        cancelBtn.onmouseover = () => cancelBtn.style.background = 'rgba(255,255,255,0.2)';
        cancelBtn.onmouseout = () => cancelBtn.style.background = 'rgba(255,255,255,0.1)';
        
        actionContainer.appendChild(enableBtn);
        actionContainer.appendChild(cancelBtn);
        
        // Add to progress section
        if (progressSection) {
            progressSection.appendChild(actionContainer);
        }
        
        // Handle Enable LLDP click
        enableBtn.onclick = async () => {
            enableBtn.disabled = true;
            enableBtn.innerHTML = `
                <div style="width: 14px; height: 14px; border: 2px solid white; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 6px;"></div>
                Enabling LLDP...
            `;
            
            try {
                // Call API to enable LLDP
                const result = await editor._enableLldpOnDevice(serial);
                
                if (result.success) {
                    if (outputDiv) {
                        outputDiv.innerHTML += `\n\n<span style="color: #27ae60;">[OK] LLDP enabled on ${result.interfaces_enabled || 'all'} interfaces!</span>\n`;
                        outputDiv.innerHTML += `<span style="color: #3498db;">Finalizing discovery...</span>\n`;
                    }
                    
                    // Brief wait -- backend already waited 10s for LLDP hellos
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    
                    // Remove action container
                    actionContainer.remove();
                    
                    // Retry discovery
                    if (outputDiv) {
                        outputDiv.innerHTML += `\n<span style="color: #FF7A33;">Retrying discovery...</span>\n`;
                    }
                    
                    // Restart discovery
                    editor.startMultiBDDiscovery(serial);
                    
                } else {
                    throw new Error(result.error || 'Failed to enable LLDP');
                }
                
            } catch (error) {
                if (outputDiv) {
                    outputDiv.innerHTML += `\n\n<span style="color: #e74c3c;">✗ Failed to enable LLDP: ${error.message}</span>\n`;
                }
                enableBtn.innerHTML = 'Failed - Try Again';
                enableBtn.disabled = false;
                enableBtn.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
            }
        };
        
        // Handle Cancel click
        cancelBtn.onclick = () => {
            actionContainer.remove();
            editor.dismissDnaasResult();
        };
    },
    
    /**
     * Enable LLDP and admin-state on all interfaces of a device.
     * Uses job-based API with polling for real-time feedback.
     * @param {string} serial - Device hostname/IP to connect to
     * @param {Object} sshConfig - Optional SSH config with user, password, skipHostKey
     */
    async _enableLldpOnDevice(serial, sshConfig = {}) {
        try {
            // Try ScalerAPI first
            if (typeof ScalerAPI !== 'undefined' && ScalerAPI.enableDeviceLldp) {
                return await ScalerAPI.enableDeviceLldp({ serial, ...sshConfig });
            }
            
            // Always use discovery_api on port 8765 for LLDP operations
            // Use current hostname for remote access support
            const apiHost = window.location.hostname || 'localhost';
            const lldpBase = `http://${apiHost}:8765/api`;
            
            // Build request with credentials
            const requestBody = {
                serial,
                username: sshConfig.user || 'dnroot',
                password: sshConfig.password || 'dnroot',
                skipHostKey: sshConfig.skipHostKey || false
            };
            
            // Start the LLDP enable job
            const startResponse = await fetch(`${lldpBase}/enable-lldp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (!startResponse.ok) {
                const err = await startResponse.json();
                throw new Error(err.error || 'API error');
            }
            
            const startResult = await startResponse.json();
            const jobId = startResult.job_id;
            
            if (!jobId) {
                throw new Error('No job ID returned');
            }
            
            // Get output div for real-time feedback
            const outputDiv = document.getElementById('dnaas-output');
            let lastLineCount = 0;
            
            // Poll for status with real-time feedback
            // Backend can take 2-3 minutes for devices with many interfaces (60+ interfaces)
            // Wait up to 4 minutes (480 attempts × 500ms = 240 seconds)
            const maxAttempts = 480; // 4 minutes max
            for (let attempt = 0; attempt < maxAttempts; attempt++) {
                await new Promise(resolve => setTimeout(resolve, 500)); // Poll every 500ms
                
                const statusResponse = await fetch(`${lldpBase}/enable-lldp/status?job_id=${encodeURIComponent(jobId)}`);
                if (!statusResponse.ok) continue;
                
                const status = await statusResponse.json();
                
                // Show new output lines in real-time
                if (outputDiv && status.output_lines && status.output_lines.length > lastLineCount) {
                    const newLines = status.output_lines.slice(lastLineCount);
                    for (const line of newLines) {
                        // Color-code the output
                        let color = '#ecf0f1'; // Default gray
                        if (line.includes('✓') || line.includes('✅')) color = '#27ae60'; // Green
                        else if (line.includes('✗') || line.includes('Error')) color = '#e74c3c'; // Red
                        else if (line.includes('⏳') || line.includes('🔧') || line.includes('📝')) color = '#FF7A33'; // Orange
                        else if (line.includes('🔌') || line.includes('📋')) color = '#3498db'; // Blue
                        
                        outputDiv.innerHTML += `<span style="color: ${color};">${line}</span>\n`;
                    }
                    lastLineCount = status.output_lines.length;
                    outputDiv.scrollTop = outputDiv.scrollHeight; // Auto-scroll
                }
                
                if (status.status === 'completed') {
                    return {
                        success: true,
                        interfaces_enabled: status.interfaces_enabled,
                        interfaces: status.interfaces,
                        already_configured: status.already_configured || false
                    };
                } else if (status.status === 'failed') {
                    throw new Error(status.error || 'LLDP enable failed');
                }
            }
            
            throw new Error('LLDP enable timed out after 4 minutes - device may have many interfaces or slow connection');
            
        } catch (error) {
            console.error('[LLDP Enable] Error:', error);
            return { success: false, error: error.message };
        }
    },
    
    /**
     * Cancel an LLDP enable operation
     */
    async _cancelLldpOnDevice(device) {
        // Use the target device if device param doesn't have job ID
        const targetDevice = (device && device._lldpJobId) ? device : editor._lldpTargetDevice;
        
        if (!targetDevice || !targetDevice._lldpJobId) {
            console.warn('[LLDP] No job to cancel');
            // Still clear any visual indicator
            if (device) editor._clearDeviceLldpStatus(device);
            if (targetDevice && targetDevice !== device) editor._clearDeviceLldpStatus(targetDevice);
            return;
        }
        
        const jobId = targetDevice._lldpJobId;
        console.log(`[LLDP] Cancelling job ${jobId}`);
        
        try {
            const apiHost = window.location.hostname || 'localhost';
            const response = await fetch(`http://${apiHost}:8765/api/enable-lldp/cancel?job_id=${jobId}`);
            const result = await response.json();
            
            if (result.status === 'cancelled' || result.error === 'Job not found') {
                // Clear the visual indicator completely (don't show error)
                editor._clearDeviceLldpStatus(targetDevice);
                // Clear last result so button returns to normal
                delete targetDevice._lastLldpResult;
                delete targetDevice._lldpJobId;
                editor.showToast('LLDP operation cancelled', 'info');
            }
        } catch (error) {
            console.error('[LLDP] Cancel failed:', error);
            // Still clear visual indicator on error
            editor._clearDeviceLldpStatus(targetDevice);
            delete targetDevice._lastLldpResult;
            delete targetDevice._lldpJobId;
        }
    },
    
    /**
     * Clear device LLDP status indicator
     */
    _clearDeviceLldpStatus(editor, device) {
        if (!editor) editor = this._getEditor();
        if (device && device._lldpStatus) {
            delete device._lldpStatus;
            if (editor) editor.draw();
        }
    },
    
    /**
     * Enable LLDP in background with visual feedback on the device node.
     * No modal dialog - just animated visual on the device and toast notifications.
     * @param {Object} device - The device object from topology
     * @param {string} serial - Device hostname/IP  
     * @param {Object} sshConfig - Optional SSH config with user, password, skipHostKey
     */
    async enableLldpBackground(editor, device, serial, sshConfig = {}) {
        this._editor = editor; // Store for internal methods
        
        // Check if already running on this device
        if (device._lldpRunning) {
            editor.showToast('LLDP enable already running on this device', 'info');
            return;
        }
        
        // Mark as running
        device._lldpRunning = true;
        
        // Check if device has connected links (including all link types and colors)
        // Simple link detection - check if device is connected to any links
        // Must match the detection in _addLinkWaveDots for consistency
        const hasLinks = editor.objects.some(obj => {
            if (!obj.type) return false;
            if (obj.type !== 'link' && obj.type !== 'unbound' && obj.type !== 'bound') return false;
            
            // device1/device2 can be either strings (device IDs) or objects
            const dev1Id = typeof obj.device1 === 'object' ? obj.device1?.id : obj.device1;
            const dev2Id = typeof obj.device2 === 'object' ? obj.device2?.id : obj.device2;
            
            return dev1Id === device.id || dev2Id === device.id;
        });
        
        console.log(`[LLDP] Device ${serial} has links: ${hasLinks}`);
        
        // Start animation on device (call internal method directly)
        this._startLldpAnimation(editor, device, hasLinks);
        
        // Show initial toast
        editor.showToast(`Enabling LLDP on ${serial}...`, 'info');
        
        try {
            // Call the LLDP enable API (internal method)
            const result = await this._enableLldpOnDevice(serial, sshConfig);
            
            // Stop animation (internal method)
            this._stopLldpAnimation(editor, device);
            device._lldpRunning = false;
            
            if (result.success) {
                if (result.already_configured) {
                    editor.showToast(`✓ LLDP already configured on ${serial} (${result.interfaces_enabled} interfaces)`, 'success');
                    device._lldpStatus = 'already_configured';
                } else {
                    editor.showToast(`✓ LLDP enabled on ${serial} (${result.interfaces_enabled} interfaces)`, 'success');
                    device._lldpStatus = 'enabled';
                }
                
                // Mark LLDP as completed with timestamp
                device.lldpEnabled = true;
                device._lldpCompletedAt = Date.now();
                
                // Brief success glow (internal method)
                this._showLldpSuccessGlow(editor, device);
                
                // Auto-open LLDP table after successful enable
                setTimeout(() => {
                    editor.showLldpTableDialog(device, serial);
                }, 800); // Small delay to let success animation play
                
            } else {
                editor.showToast(`✗ LLDP failed on ${serial}: ${result.error}`, 'error');
                device._lldpStatus = 'failed';
                this._showLldpFailureGlow(editor, device);
            }
            
        } catch (error) {
            // Stop animation on error (internal method)
            this._stopLldpAnimation(editor, device);
            device._lldpRunning = false;
            device._lldpStatus = 'failed';
            
            editor.showToast(`✗ LLDP error on ${serial}: ${error.message}`, 'error');
            this._showLldpFailureGlow(editor, device);
        }
        
        // Redraw to clear any visual state
        editor.draw();
    },
    
    /**
     * Start LLDP animation on device node.
     * Uses canvas-based animation for automatic device tracking
     */
    _startLldpAnimation(editor, device, hasLinks) {
        device._lldpAnimating = true;
        device._lldpRunning = true;
        device._lldpHasLinks = hasLinks;
        device._lldpAnimStart = Date.now();
        
        // Start lightweight animation timer (just redraws, doesn't block events)
        this._startLldpAnimationTimer(editor);
    },
    
    /**
     * Start lightweight animation timer for LLDP effects
     * Uses setInterval instead of requestAnimationFrame to avoid blocking
     */
    _startLldpAnimationTimer(editor) {
        // Check if already running
        if (editor._lldpAnimTimer) return;
        
        // Use setInterval for predictable, non-blocking animation
        editor._lldpAnimTimer = setInterval(() => {
            // Check if any device is animating
            const hasAnimatingDevice = editor.objects.some(o => 
                o.type === 'device' && o._lldpAnimating
            );
            
            if (hasAnimatingDevice) {
                editor.draw(); // Redraw canvas
            } else {
                // Stop timer when no devices animating
                clearInterval(editor._lldpAnimTimer);
                editor._lldpAnimTimer = null;
            }
        }, 50); // 20fps is smooth enough for this animation
    },
    
    /**
     * Stop LLDP animation on device and clear animation state
     */
    _stopLldpAnimation(editor, device) {
        device._lldpAnimating = false;
        device._lldpRunning = false;
        device._lldpAnimStart = null;
        device._lldpWavePhase = 0;
        device._lldpHasLinks = false;
        
        // Check if any other device is still animating
        const hasOtherAnimating = editor.objects.some(o => 
            o.type === 'device' && o._lldpAnimating && o.id !== device.id
        );
        
        // Stop timer if no more animating devices
        if (!hasOtherAnimating && editor._lldpAnimTimer) {
            clearInterval(editor._lldpAnimTimer);
            editor._lldpAnimTimer = null;
        }
        
        // Clean up any old CSS elements that might exist (internal method)
        this._removeSimpleLldpAnimation(editor, device);
        
        // Trigger a final redraw
        editor.draw();
    },
    
    /**
     * Create LLDP animation using CSS
     * - Device WITH links: pulsing border + wave dots traveling along links
     * - Device WITHOUT links (isolated): simple pulsing border only
     * Color: Cyan #00D4AA
     * 
     * IMPORTANT: Animation is removed on any pan/zoom and must be recreated
     */
    _createSimpleLldpAnimation(device, hasLinks) {
        const editor = this._getEditor();
        if (!editor) return;
        
        console.log(`[LLDP Animation] Creating for ${device.label}, hasLinks: ${hasLinks}`);
        this._removeSimpleLldpAnimation(editor, device);
        
        // Add CSS keyframes if not present
        if (!document.getElementById('lldp-anim-css')) {
            const style = document.createElement('style');
            style.id = 'lldp-anim-css';
            style.textContent = `
                @keyframes lldpPulse {
                    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
                    50% { transform: translate(-50%, -50%) scale(1.05); opacity: 0.5; }
                }
                @keyframes lldpDotTravel {
                    0% { offset-distance: 0%; opacity: 1; }
                    100% { offset-distance: 100%; opacity: 0.3; }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Calculate screen position correctly
        const rect = editor.canvas.getBoundingClientRect();
        const screenX = rect.left + (device.x * editor.zoom + editor.panOffset.x);
        const screenY = rect.top + (device.y * editor.zoom + editor.panOffset.y);
        const screenR = (device.radius || device.r || 25) * editor.zoom;
        
        console.log(`[LLDP Animation] Screen pos: (${Math.round(screenX)}, ${Math.round(screenY)}), R: ${Math.round(screenR)}`);
        
        // Create main container at device position
        const container = document.createElement('div');
        container.id = `lldp-anim-${device.id}`;
        container.className = 'lldp-animation-container';
        container.style.cssText = `
            position: fixed;
            left: ${screenX}px;
            top: ${screenY}px;
            width: 0;
            height: 0;
            pointer-events: none;
            z-index: 1000;
        `;
        
        // ALWAYS: Pulsing cyan border ring around device
        const pulseRing = document.createElement('div');
        const ringSize = screenR * 2 + 8;
        pulseRing.style.cssText = `
            position: absolute;
            left: 50%;
            top: 50%;
            width: ${ringSize}px;
            height: ${ringSize}px;
            border-radius: 50%;
            border: 3px solid #00D4AA;
            box-shadow: 0 0 12px rgba(0, 212, 170, 0.6);
            animation: lldpPulse 1s ease-in-out infinite;
        `;
        container.appendChild(pulseRing);
        
        document.body.appendChild(container);
        device._lldpAnimElement = container;
        
        // If device has links, add wave dots traveling along them
        if (hasLinks) {
            editor._addLinkWaveDots(device, rect, screenR);
        }
        
        console.log(`[LLDP Animation] Created for ${device.label}`);
    },
    
    /**
     * Add traveling dot waves along ALL connected links
     * Dots emit FROM the initiating device OUTWARD along each link's visual path
     */
    _addLinkWaveDots(device, rect) {
        // Find ALL links connected to this device (any type - no special handling)
        const connectedLinks = editor.objects.filter(obj => {
            if (!obj.type) return false;
            if (obj.type !== 'link' && obj.type !== 'unbound' && obj.type !== 'bound') return false;
            
            // Check if device is connected to this link
            // Handle both: device1 as object ref (device1.id) AND as ID string (device1)
            const dev1Id = typeof obj.device1 === 'object' ? obj.device1?.id : obj.device1;
            const dev2Id = typeof obj.device2 === 'object' ? obj.device2?.id : obj.device2;
            
            if (dev1Id === device.id || dev2Id === device.id) return true;
            
            return false;
        }).slice(0, 10); // Limit to 10 links for performance
        
        console.log(`[LLDP Wave] Device ${device.label}: ${connectedLinks.length} connected links`);
        
        if (connectedLinks.length === 0) return;
        
        // Create SVG overlay covering the canvas area
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.id = `lldp-wave-svg-${device.id}`;
        svg.style.cssText = `
            position: fixed;
            left: ${rect.left}px;
            top: ${rect.top}px;
            width: ${rect.width}px;
            height: ${rect.height}px;
            pointer-events: none;
            overflow: visible;
            z-index: 999;
        `;
        
        let dotsCreated = 0;
        
        connectedLinks.forEach((link, idx) => {
            // Determine start (device) and end (target) positions
            let targetX, targetY;
            
            // Get device IDs (handle both object refs and ID strings)
            const dev1Id = typeof link.device1 === 'object' ? link.device1?.id : link.device1;
            const dev2Id = typeof link.device2 === 'object' ? link.device2?.id : link.device2;
            
            // Find the target device (the OTHER end of the link)
            let targetDeviceId;
            if (dev1Id === device.id) {
                targetDeviceId = dev2Id;
            } else if (dev2Id === device.id) {
                targetDeviceId = dev1Id;
            } else {
                return; // Skip if device not connected
            }
            
            // Find target device object to get its position
            const targetDevice = editor.objects.find(o => o.type === 'device' && o.id === targetDeviceId);
            if (!targetDevice) {
                console.log(`[LLDP Wave] Could not find target device ${targetDeviceId}`);
                return; // Skip if target device not found
            }
            
            targetX = targetDevice.x;
            targetY = targetDevice.y;
            
            // Convert world coords to screen coords (relative to canvas)
            const startSX = device.x * editor.zoom + editor.panOffset.x;
            const startSY = device.y * editor.zoom + editor.panOffset.y;
            const endSX = targetX * editor.zoom + editor.panOffset.x;
            const endSY = targetY * editor.zoom + editor.panOffset.y;
            
            // Build SVG path - check if link has curve control points
            let pathD;
            if (link.curveOffset && link.curveOffset !== 0) {
                // Curved link - calculate quadratic bezier control point
                const midX = (startSX + endSX) / 2;
                const midY = (startSY + endSY) / 2;
                const dx = endSX - startSX;
                const dy = endSY - startSY;
                const len = Math.sqrt(dx * dx + dy * dy);
                const nx = -dy / len;
                const ny = dx / len;
                const ctrlX = midX + nx * link.curveOffset * editor.zoom;
                const ctrlY = midY + ny * link.curveOffset * editor.zoom;
                pathD = `M ${startSX} ${startSY} Q ${ctrlX} ${ctrlY} ${endSX} ${endSY}`;
            } else {
                // Straight line
                pathD = `M ${startSX} ${startSY} L ${endSX} ${endSY}`;
            }
            
            // Create 2 traveling dots per link
            for (let i = 0; i < 2; i++) {
                const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                dot.setAttribute('r', '6');
                dot.setAttribute('fill', '#00D4AA');
                dot.setAttribute('filter', 'drop-shadow(0 0 4px #00D4AA)');
                dot.style.cssText = `
                    offset-path: path('${pathD}');
                    animation: lldpDotTravel 1.5s ease-in-out infinite;
                    animation-delay: ${i * 0.75 + idx * 0.2}s;
                `;
                svg.appendChild(dot);
                dotsCreated++;
            }
        });
        
        console.log(`[LLDP Wave] Created ${dotsCreated} traveling dots`);
        
        if (dotsCreated > 0) {
            document.body.appendChild(svg);
            // Store reference for cleanup
            device._lldpWaveSvg = svg;
        }
    },
    
    /**
     * Remove LLDP animation elements (both pulse ring and wave dots)
     */
    _removeSimpleLldpAnimation(editor, device) {
        // Remove pulse ring container
        if (device._lldpAnimElement) {
            try {
                if (device._lldpAnimElement.parentNode) {
                    device._lldpAnimElement.parentNode.removeChild(device._lldpAnimElement);
                }
            } catch (e) {
                console.warn(`[LLDP Animation] Could not remove pulse ring:`, e);
            }
            device._lldpAnimElement = null;
        }
        
        // Remove wave SVG
        if (device._lldpWaveSvg) {
            try {
                if (device._lldpWaveSvg.parentNode) {
                    device._lldpWaveSvg.parentNode.removeChild(device._lldpWaveSvg);
                }
            } catch (e) {
                console.warn(`[LLDP Animation] Could not remove wave SVG:`, e);
            }
            device._lldpWaveSvg = null;
        }
        
        // Cleanup by ID as fallback
        const existing = document.getElementById(`lldp-anim-${device.id}`);
        if (existing && existing.parentNode) {
            existing.parentNode.removeChild(existing);
        }
        const waveSvg = document.getElementById(`lldp-wave-svg-${device.id}`);
        if (waveSvg && waveSvg.parentNode) {
            waveSvg.parentNode.removeChild(waveSvg);
        }
    },
    
    /**
     * Show brief success glow on device
     */
    _showLldpSuccessGlow(editor, device) {
        device._lldpSuccessGlow = true;
        device._lldpSuccessStart = Date.now();
        setTimeout(() => {
            device._lldpSuccessGlow = false;
            editor.draw();
        }, 2000);
    },
    
    /**
     * Show brief failure glow on device  
     */
    _showLldpFailureGlow(editor, device) {
        device._lldpFailureGlow = true;
        device._lldpFailureStart = Date.now();
        setTimeout(() => {
            device._lldpFailureGlow = false;
            editor.draw();
        }, 2000);
    },
    
    /**
     * Animation loop for LLDP effects on all devices
     * DISABLED: Animation was causing issues
     */
    _animateLldpEffects() {
        // Disabled - animation shown via button CSS only
        const editor = this._getEditor();
        if (editor) editor._lldpAnimationFrame = null;
    },
    
    /**
     * Draw LLDP animation effects for a device (called from drawDevice)
     * Canvas-based animation that automatically follows device position/size
     */
    _drawLldpEffects(editor, device) {
        if (!device) return;
        
        const ctx = editor.ctx;
        const x = device.x;
        const y = device.y;
        const r = device.radius || device.r || 25;
        
        // Success glow (green pulse)
        if (device._lldpSuccessGlow) {
            const elapsed = (Date.now() - device._lldpSuccessStart) / 1000;
            const alpha = Math.max(0, 0.6 - elapsed * 0.3);
            const scale = 1 + elapsed * 0.5;
            
            ctx.save();
            ctx.beginPath();
            ctx.arc(x, y, r * scale, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(39, 174, 96, ${alpha})`;
            ctx.lineWidth = 4;
            ctx.stroke();
            ctx.restore();
        }
        
        // Failure glow (red pulse)
        if (device._lldpFailureGlow) {
            const elapsed = (Date.now() - device._lldpFailureStart) / 1000;
            const alpha = Math.max(0, 0.6 - elapsed * 0.3);
            const scale = 1 + elapsed * 0.3;
            
            ctx.save();
            ctx.beginPath();
            ctx.arc(x, y, r * scale, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(231, 76, 60, ${alpha})`;
            ctx.lineWidth = 4;
            ctx.stroke();
            ctx.restore();
        }
        
        // Active LLDP animation - CANVAS-BASED for automatic device tracking
        if (device._lldpAnimating) {
            const elapsed = Date.now() - (device._lldpAnimStart || Date.now());
            const phase = (elapsed / 1500) % 1; // 1.5s cycle
            
            ctx.save();
            
            // Draw pulsing cyan border ring around device
            const pulseScale = 1 + 0.1 * Math.sin(elapsed / 200);
            ctx.beginPath();
            ctx.arc(x, y, r * pulseScale + 4, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 212, 170, 0.8)';
            ctx.lineWidth = 3;
            ctx.shadowColor = '#00D4AA';
            ctx.shadowBlur = 10;
            ctx.stroke();
            ctx.shadowBlur = 0;
            
            // If device has connected links, draw wave dots along them
            if (device._lldpHasLinks) {
                editor._drawCanvasWaveDots(device, phase);
            } else {
                // For isolated devices, draw expanding rings
                editor._drawPulsingGlow(device, phase);
            }
            
            ctx.restore();
        }
    },
    
    /**
     * Draw traveling dots along connected links (canvas-based)
     * Uses the actual link control points for accurate curve following
     */
    _drawCanvasWaveDots(editor, device, phase) {
        const ctx = editor.ctx;
        const x = device.x;
        const y = device.y;
        const r = device.radius || device.r || 25;
        
        // Find connected links
        const connectedLinks = editor.objects.filter(obj => {
            if (!obj.type || (obj.type !== 'link' && obj.type !== 'unbound' && obj.type !== 'bound')) return false;
            const dev1Id = typeof obj.device1 === 'object' ? obj.device1?.id : obj.device1;
            const dev2Id = typeof obj.device2 === 'object' ? obj.device2?.id : obj.device2;
            return dev1Id === device.id || dev2Id === device.id;
        }).slice(0, 10);
        
        ctx.save();
        
        connectedLinks.forEach((link, idx) => {
            const dev1Id = typeof link.device1 === 'object' ? link.device1?.id : link.device1;
            const dev2Id = typeof link.device2 === 'object' ? link.device2?.id : link.device2;
            
            // Find target device
            const targetDeviceId = dev1Id === device.id ? dev2Id : dev1Id;
            const targetDevice = editor.objects.find(o => o.type === 'device' && o.id === targetDeviceId);
            if (!targetDevice) return;
            
            const targetR = targetDevice.radius || targetDevice.r || 25;
            
            // Use the link's pre-calculated rendered endpoints if available
            let startX, startY, endX, endY;
            
            if (link._renderedEndpoints) {
                // Use actual rendered endpoints from the link drawing
                const ep = link._renderedEndpoints;
                // Determine direction: dots should go FROM initiator TO target
                const isInitiatorDev1 = dev1Id === device.id;
                if (isInitiatorDev1) {
                    startX = ep.startX;
                    startY = ep.startY;
                    endX = ep.endX;
                    endY = ep.endY;
                } else {
                    // Reverse: initiator is dev2
                    startX = ep.endX;
                    startY = ep.endY;
                    endX = ep.startX;
                    endY = ep.startY;
                }
            } else {
                // Fallback: calculate from device centers
                const dx = targetDevice.x - x;
                const dy = targetDevice.y - y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 1) return;
                
                const dirX = dx / dist;
                const dirY = dy / dist;
                
                startX = x + dirX * r;
                startY = y + dirY * r;
                endX = targetDevice.x - dirX * targetR;
                endY = targetDevice.y - dirY * targetR;
            }
            
            // Get control points if link has them (cubic bezier)
            const hasCurve = link._cp1 && link._cp2;
            let cp1x, cp1y, cp2x, cp2y;
            
            if (hasCurve) {
                const isInitiatorDev1 = dev1Id === device.id;
                if (isInitiatorDev1) {
                    cp1x = link._cp1.x;
                    cp1y = link._cp1.y;
                    cp2x = link._cp2.x;
                    cp2y = link._cp2.y;
                } else {
                    // Reverse control points for opposite direction
                    cp1x = link._cp2.x;
                    cp1y = link._cp2.y;
                    cp2x = link._cp1.x;
                    cp2y = link._cp1.y;
                }
            }
            
            // Draw 2 dots per link at different phases
            for (let i = 0; i < 2; i++) {
                const dotPhase = (phase + i * 0.5 + idx * 0.15) % 1;
                
                let dotX, dotY;
                const t = dotPhase;
                
                if (hasCurve) {
                    // Cubic Bezier: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
                    const oneMinusT = 1 - t;
                    const t2 = t * t;
                    const t3 = t2 * t;
                    const oneMinusT2 = oneMinusT * oneMinusT;
                    const oneMinusT3 = oneMinusT2 * oneMinusT;
                    
                    dotX = oneMinusT3 * startX + 
                           3 * oneMinusT2 * t * cp1x + 
                           3 * oneMinusT * t2 * cp2x + 
                           t3 * endX;
                    dotY = oneMinusT3 * startY + 
                           3 * oneMinusT2 * t * cp1y + 
                           3 * oneMinusT * t2 * cp2y + 
                           t3 * endY;
                } else {
                    // Straight line
                    dotX = startX + (endX - startX) * t;
                    dotY = startY + (endY - startY) * t;
                }
                
                // Draw dot with glow
                ctx.beginPath();
                ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(0, 212, 170, 0.9)';
                ctx.shadowColor = '#00D4AA';
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        });
        
        ctx.restore();
    },
    
    /**
     * Draw pulsing glow waves FROM device borders outward (for devices without links)
     */
    _drawPulsingGlow(editor, device, phase) {
        const ctx = editor.ctx;
        const x = device.x;
        const y = device.y;
        const r = device.radius || device.r || 25;
        
        ctx.save();
        
        // Draw 2 simple expanding rings (minimal overhead)
        for (let i = 0; i < 2; i++) {
            const ringPhase = (phase + i * 0.5) % 1;
            const ringRadius = r + (ringPhase * r * 1.5);
            const alpha = Math.max(0, 0.4 * (1 - ringPhase));
            const lineWidth = Math.max(1, 2.5 * (1 - ringPhase));
            
            ctx.beginPath();
            ctx.arc(x, y, ringRadius, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(0, 180, 216, ${alpha})`;
            ctx.lineWidth = lineWidth;
            ctx.stroke();
        }
        
        ctx.restore();
    },
    
    /**
     * Draw outgoing waves traveling ALONG connected links away from device
     * Waves emit from where links connect to device and travel outward along each link
     */
    _drawOutgoingWaves(editor, device, phase) {
        const ctx = editor.ctx;
        const x = device.x;
        const y = device.y;
        const r = device.radius || device.r || 25;
        const proximityThreshold = r + 35;
        
        // Find connected links (including proximity-based for all links)
        const connectedLinks = editor.objects.filter(obj => {
            // Accept ANY object that could be a link (including orange ISIS links)
            if (!obj.type) return false;
            const isLinkType = obj.type === 'link' || obj.type === 'unbound' || obj.type === 'bound';
            if (!isLinkType) return false;
            
            // Check device references (object refs or IDs)
            const dev1Id = obj.device1?.id || obj.device1Id || obj.device1;
            const dev2Id = obj.device2?.id || obj.device2Id || obj.device2;
            const srcId = obj.source?.id || obj.sourceId;
            const tgtId = obj.target?.id || obj.targetId;
            
            if (dev1Id === device.id || dev2Id === device.id ||
                srcId === device.id || tgtId === device.id) {
                return true;
            }
            
            // Check proximity for ALL links (including bound links with start/end)
            // This catches links that may have broken references after page load
            if (obj.start && obj.end) {
                const d1 = Math.hypot(obj.start.x - x, obj.start.y - y);
                const d2 = Math.hypot(obj.end.x - x, obj.end.y - y);
                if (d1 <= proximityThreshold || d2 <= proximityThreshold) {
                    return true;
                }
            }
            
            // Also check device1/device2 x,y coordinates for bound links
            if (obj.device1 && obj.device2) {
                // Handle both object refs and direct device objects
                const dev1 = typeof obj.device1 === 'object' ? obj.device1 : editor.objects.find(o => o.id === obj.device1);
                const dev2 = typeof obj.device2 === 'object' ? obj.device2 : editor.objects.find(o => o.id === obj.device2);
                
                if (dev1 && dev2) {
                    const d1 = Math.hypot(dev1.x - x, dev1.y - y);
                    const d2 = Math.hypot(dev2.x - x, dev2.y - y);
                    if (d1 <= proximityThreshold || d2 <= proximityThreshold) {
                        return true;
                    }
                }
            }
            
            return false;
        });
        
        ctx.save();
        
        if (connectedLinks.length > 0) {
            // Draw waves along each connected link
            connectedLinks.forEach(link => {
                let targetX, targetY;
                
                // Find the other end of the link
                if (link.device1 && link.device1.id === device.id && link.device2) {
                    targetX = link.device2.x;
                    targetY = link.device2.y;
                } else if (link.device2 && link.device2.id === device.id && link.device1) {
                    targetX = link.device1.x;
                    targetY = link.device1.y;
                } else if (link.source && link.source.id === device.id && link.target) {
                    targetX = link.target.x;
                    targetY = link.target.y;
                } else if (link.target && link.target.id === device.id && link.source) {
                    targetX = link.source.x;
                    targetY = link.source.y;
                } else if (link.start && link.end) {
                    // Unbound link - find which end is closer to device
                    const d1 = Math.hypot(link.start.x - x, link.start.y - y);
                    const d2 = Math.hypot(link.end.x - x, link.end.y - y);
                    if (d1 < d2) {
                        targetX = link.end.x;
                        targetY = link.end.y;
                    } else {
                        targetX = link.start.x;
                        targetY = link.start.y;
                    }
                } else {
                    return;
                }
                
                // Calculate direction from device to target
                const dx = targetX - x;
                const dy = targetY - y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 1) return;
                
                const dirX = dx / dist;
                const dirY = dy / dist;
                
                // Start point: where link meets device border
                const startX = x + dirX * r;
                const startY = y + dirY * r;
                
                // Find target device to get its actual radius
                let targetR = 25; // Default target device radius
                const targetDevice = editor.objects.find(obj => 
                    obj.type === 'device' && 
                    Math.hypot(obj.x - targetX, obj.y - targetY) < 10 // Closer match tolerance
                );
                if (targetDevice) {
                    targetR = targetDevice.radius || targetDevice.r || 25;
                }
                
                // Max travel distance: stop exactly AT target device border
                const maxTravel = dist - r - targetR;
                if (maxTravel < 10) return; // Link too short
                
                // Draw 2 wave pulses traveling along the link (simple, fast)
                for (let i = 0; i < 2; i++) {
                    const wavePhase = ((phase * 1.0) + i * 0.5) % 1;
                    const travelDist = wavePhase * maxTravel;
                    
                    const pulseX = startX + dirX * travelDist;
                    const pulseY = startY + dirY * travelDist;
                    const perpX = -dirY;
                    const perpY = dirX;
                    
                    // Fade out as wave travels
                    const alpha = Math.max(0, 0.5 - wavePhase * 0.5);
                    const pulseWidth = Math.max(1.5, 3.5 - wavePhase * 2);
                    const pulseLength = 8 + (1 - wavePhase) * 5;
                    
                    ctx.beginPath();
                    ctx.moveTo(pulseX - perpX * pulseLength, pulseY - perpY * pulseLength);
                    ctx.lineTo(pulseX + perpX * pulseLength, pulseY + perpY * pulseLength);
                    ctx.strokeStyle = `rgba(0, 180, 216, ${alpha})`;
                    ctx.lineWidth = pulseWidth;
                    ctx.lineCap = 'round';
                    ctx.stroke();
                }
            });
        } else {
            // Fallback to pulsing glow if no links found
            editor._drawPulsingGlow(device, phase);
        }
        
        // Draw subtle glow on the device border itself
        ctx.save();
        const borderAlpha = 0.35 + Math.sin(phase * Math.PI * 2) * 0.25;
        ctx.shadowColor = `rgba(0, 180, 216, ${borderAlpha * 0.8})`;
        ctx.shadowBlur = 12;
        ctx.strokeStyle = `rgba(0, 180, 216, ${borderAlpha})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    },
    
    /**
     * Show DNAAS topology selector dialog
     */
    showTopologySelector(editor, topologies) {
        const dialog = document.createElement('div');
        dialog.id = 'dnaas-topology-dialog';
        dialog.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(8px);
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const topologiesHTML = topologies.reverse().map((topo, idx) => {
            const date = new Date(topo.timestamp);
            const timeAgo = editor.getTimeAgo(date);
            return `
                <button class="dnaas-topo-item" data-index="${topologies.length - 1 - idx}" style="
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    border: 1px solid ${editor.darkMode ? 'rgba(255,94,31,0.3)' : 'rgba(255,94,31,0.2)'};
                    border-radius: 8px;
                    background: ${editor.darkMode ? 'rgba(255,94,31,0.05)' : 'rgba(255,94,31,0.03)'};
                    cursor: pointer;
                    transition: all 0.15s ease;
                    width: 100%;
                    text-align: left;
                ">
                    <svg viewBox="0 0 24 24" width="32" height="32" style="flex-shrink: 0;">
                        <circle cx="6" cy="12" r="2.5" fill="#FF5E1F"/><circle cx="18" cy="6" r="2.5" fill="#FF5E1F"/><circle cx="18" cy="18" r="2.5" fill="#FF5E1F"/>
                        <path d="M9 12h6M15 8l-6 4M15 16l-6-4" stroke="#FF5E1F" stroke-width="1.5" fill="none"/>
                    </svg>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: ${editor.darkMode ? '#fff' : '#1a1a1a'}; margin-bottom: 4px;">${topo.name}</div>
                        <div style="font-size: 11px; color: ${editor.darkMode ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.5)'};">
                            ${topo.deviceCount || 0} devices, ${topo.linkCount || 0} links • ${timeAgo}
                        </div>
                    </div>
                </button>
            `;
        }).join('');
        
        dialog.innerHTML = `
            <div style="
                background: ${editor.darkMode ? 'rgba(15, 15, 25, 0.95)' : 'rgba(255, 255, 255, 0.95)'};
                backdrop-filter: blur(24px) saturate(200%);
                border: 1px solid ${editor.darkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};
                border-radius: 16px;
                padding: 24px;
                max-width: 600px;
                width: 90vw;
                max-height: 80vh;
                display: flex;
                flex-direction: column;
                box-shadow: 0 12px 48px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                    <h3 style="margin: 0; color: ${editor.darkMode ? '#fff' : '#1a1a1a'}; font-size: 18px;">Load DNAAS Topology</h3>
                    <button id="close-dnaas-selector" style="
                        border: none;
                        background: none;
                        color: ${editor.darkMode ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)'};
                        cursor: pointer;
                        font-size: 24px;
                        padding: 0;
                        width: 32px;
                        height: 32px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 6px;
                    ">&times;</button>
                </div>
                <div style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;">
                    ${topologiesHTML}
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        document.getElementById('close-dnaas-selector').onclick = () => dialog.remove();
        dialog.onclick = (e) => {
            if (e.target === dialog) dialog.remove();
        };
        
        const items = dialog.querySelectorAll('.dnaas-topo-item');
        items.forEach(item => {
            item.onclick = () => {
                const index = parseInt(item.dataset.index);
                const topo = topologies[index];
                dialog.remove();
                editor.loadTopologyFromData(topo.data);
                editor.showToast(`Loaded "${topo.name}"`, 'success');
            };
        });
    },

    /**
     * Show dialog for tracing path by serial number
     */
    showTraceDialog(editor) {
        editor.showInputDialog(
            'DNAAS Path Discovery - Enter Device Serial',
            'e.g., wk31d7vv00023 or 100.64.0.220',
            (serial1) => {
                if (!serial1) return;
                
                editor.showInputDialog(
                    'Enter Second Device (Optional)',
                    'Leave empty for single device discovery',
                    (serial2) => {
                        const cmd = serial2
                            ? `python3 /home/dn/CURSOR/dnaas_path_discovery.py ${serial1} ${serial2}`
                            : `python3 /home/dn/CURSOR/dnaas_path_discovery.py ${serial1}`;
                        
                        if (navigator.clipboard) {
                            navigator.clipboard.writeText(cmd).then(() => {
                                editor.showToast('Command copied to clipboard!', 'success');
                            }).catch(() => {});
                        }
                        
                        const msg = 
                            'Run this command in terminal:\n\n' +
                            `  ${cmd}\n\n` +
                            'Output files will be saved to output/dnaas_path_<timestamp>.json';
                        
                        editor.showInfoDialog('DNAAS Path Discovery', msg);
                        
                        if (editor.debugger) {
                            editor.debugger.logInfo(`DNAAS trace: ${cmd}`);
                        }
                    },
                    ''
                );
            }
        );
    },

    /**
     * Show dialog for finding Bridge Domains
     */
    showFindBDsDialog(editor) {
        editor.showInputDialog(
            'Find Bridge Domains - Enter Device Serial',
            'e.g., wk31d7vv00023',
            (deviceSerial) => {
                if (!deviceSerial) return;
                
                const discoveryCmd = `python3 /home/dn/CURSOR/dnaas_path_discovery.py ${deviceSerial}`;
                
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(discoveryCmd).then(() => {
                        editor.showToast('Discovery command copied!', 'success');
                    }).catch(() => {});
                }
                
                const msg = 
                    '1. Run Discovery Script:\n\n' +
                    `   ${discoveryCmd}\n\n` +
                    '2. SSH to device and run:\n\n' +
                    '   show network-services bridge domain | no-more\n' +
                    '   show network-services evpn instance | no-more';
                
                editor.showInfoDialog('Find Bridge Domains', msg);
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`DNAAS BD search: ${deviceSerial}`);
                }
            }
        );
    },

    /**
     * Show DNAAS device inventory dialog
     * Extracted from topology.js for modular architecture
     */
    showInventoryDialog(editor) {
        const paths = ['/device_inventory.json', 'device_inventory.json', './device_inventory.json'];
        
        const tryPath = (index) => {
            if (index >= paths.length) {
                const msg = 'Device inventory not found.\n\nRun a path discovery first:\npython3 /home/dn/CURSOR/dnaas_path_discovery.py <serial>\n\nThen refresh this page.';
                editor.showInfoDialog('Device Inventory', msg);
                return;
            }
            
            fetch(paths[index])
                .then(response => {
                    if (!response.ok) throw new Error('Not found');
                    return response.json();
                })
                .then(data => {
                    const devices = data.devices || {};
                    const deviceCount = Object.keys(devices).length;
                    
                    if (deviceCount === 0) {
                        editor.showInfoDialog('Device Inventory', 'Device inventory is empty.\n\nRun a path discovery to populate:\npython3 /home/dn/CURSOR/dnaas_path_discovery.py <serial>');
                        return;
                    }
                    
                    let msg = `Found ${deviceCount} device(s):\n` + '─'.repeat(45) + '\n\n';
                    Object.entries(devices).forEach(([serial, info]) => {
                        const dnaasCount = (info.dnaas_interfaces || []).length;
                        const hostname = info.hostname || 'Unknown';
                        msg += `▸ ${hostname}\n    Serial: ${serial}\n    Mgmt IP: ${info.mgmt_ip || 'N/A'}\n    DNAAS Interfaces: ${dnaasCount}\n`;
                        if (info.dnaas_interfaces && info.dnaas_interfaces.length > 0) {
                            msg += `      → ${info.dnaas_interfaces.join(', ')}\n`;
                        }
                        msg += '\n';
                    });
                    
                    editor.showInfoDialog('DNAAS Device Inventory', msg);
                })
                .catch(() => tryPath(index + 1));
        };
        
        tryPath(0);
    },

    /**
     * Show DNAAS path devices dialog - all devices on canvas organized by type
     * Extracted from topology.js for modular architecture
     */
    showPathDevicesDialog(editor) {
        const devices = editor.objects.filter(o => o.type === 'device');
        
        if (devices.length === 0) {
            editor.showInfoDialog('Path Devices', 'No devices on canvas.\n\nRun a DNAAS discovery first to populate the topology.');
            return;
        }
        
        const devicesByType = { 'SuperSpine': [], 'Spine': [], 'Leaf': [], 'PE/Router': [], 'Other': [] };
        
        devices.forEach(d => {
            const label = (d.label || d.id || '').toUpperCase();
            const hasSSH = d.sshConfig && (d.sshConfig.host || d.sshConfig.hostBackup);
            const hasSN = d.deviceSerial && d.deviceSerial.trim() !== '';
            
            const deviceEntry = {
                label: d.label || d.id,
                sshHost: d.sshConfig?.host || '',
                sshBackup: d.sshConfig?.hostBackup || '',
                serial: d.deviceSerial || '',
                hasSSH, hasSN,
                user: d.sshConfig?.user || 'dnroot'
            };
            
            if (label.includes('SUPERSPINE')) devicesByType['SuperSpine'].push(deviceEntry);
            else if (label.includes('SPINE')) devicesByType['Spine'].push(deviceEntry);
            else if (label.includes('LEAF')) devicesByType['Leaf'].push(deviceEntry);
            else if (label.includes('PE') || label.includes('ROUTER') || label.includes('NCP') || label.includes('NCF')) devicesByType['PE/Router'].push(deviceEntry);
            else devicesByType['Other'].push(deviceEntry);
        });
        
        let msg = `📊 DNAAS Path Devices Summary\nTotal: ${devices.length} device(s)\n` + '═'.repeat(50) + '\n\n';
        
        for (const [type, devs] of Object.entries(devicesByType)) {
            if (devs.length === 0) continue;
            const icon = type === 'SuperSpine' ? '🔴' : type === 'Spine' ? '🟣' : type === 'Leaf' ? '🟠' : type === 'PE/Router' ? '🔵' : '⚪';
            msg += `${icon} ${type} (${devs.length})\n` + '─'.repeat(40) + '\n';
            
            devs.forEach(d => {
                const sshIcon = d.hasSSH ? '✅' : '❌';
                msg += `  ${sshIcon} ${d.label}\n`;
                if (d.sshHost) msg += `      IP: ${d.sshHost}\n`;
                if (d.serial || d.sshBackup) msg += `      SN: ${d.serial || d.sshBackup}\n`;
                if (!d.hasSSH && !d.hasSN) msg += `      ⚠️ No SSH credentials\n`;
            });
            msg += '\n';
        }
        
        const withSSH = devices.filter(d => d.sshConfig && (d.sshConfig.host || d.sshConfig.hostBackup)).length;
        const withoutSSH = devices.length - withSSH;
        msg += '═'.repeat(50) + `\n✅ With SSH: ${withSSH}  |  ❌ Without SSH: ${withoutSSH}\n`;
        if (withoutSSH > 0) msg += '\n💡 Tip: Right-click a device → "Set SSH Address" to add credentials';
        
        editor.showInfoDialog('DNAAS Path Devices', msg);
    },

    /**
     * Load predefined DNAAS example topology
     * Extracted from topology.js for modular architecture
     */
    loadPredefinedDnaasTopology(editor, topologyType) {
        let topologyData = null;
        
        switch(topologyType) {
            case 'logical-bd210':
                topologyData = editor.getDnaasLogicalBD210Topology();
                break;
            case 'bd210':
                topologyData = editor.getDnaasBD210Topology();
                break;
            case 'discover':
                editor.showInfoDialog('Live Network Discovery', 
                    'This feature will connect to network devices and\n' +
                    'discover the topology automatically.\n\n' +
                    'Coming soon!\n\n' +
                    'For now, use "Trace Path by Serial Number" to\n' +
                    'run the discovery script manually.');
                return;
            default:
                console.warn('Unknown DNAAS topology type:', topologyType);
                return;
        }
        
        if (topologyData) {
            if (editor.objects.length > 0) {
                if (!confirm('This will replace the current canvas. Continue?')) return;
            }
            
            editor.saveState();
            editor.objects = topologyData.objects || [];
            editor.deviceIdCounter = topologyData.metadata?.deviceIdCounter || 0;
            editor.linkIdCounter = topologyData.metadata?.linkIdCounter || 0;
            editor.textIdCounter = topologyData.metadata?.textIdCounter || 0;
            
            editor.selectedObject = null;
            editor.selectedObjects = [];
            editor.zoom = 1;
            
            const devices = editor.objects.filter(o => o.type === 'device');
            if (devices.length > 0) {
                const centerX = devices.reduce((sum, d) => sum + d.x, 0) / devices.length;
                const centerY = devices.reduce((sum, d) => sum + d.y, 0) / devices.length;
                editor.panOffset = {
                    x: ((editor.canvasW || editor.canvas.width) / 2) - centerX,
                    y: ((editor.canvasH || editor.canvas.height) / 2) - centerY
                };
            } else {
                editor.panOffset = { x: 0, y: 0 };
            }
            
            localStorage.setItem('topology_zoom', editor.zoom.toString());
            localStorage.setItem('topology_panOffset', JSON.stringify(editor.panOffset));
            
            editor.updatePropertiesPanel();
            editor.updateZoomIndicator();
            editor.draw();
            
            console.log(`📡 DNAAS topology loaded: ${topologyType}`, {
                objects: editor.objects.length,
                devices: devices.length,
                panOffset: editor.panOffset
            });
            
            if (editor.debugger) {
                editor.debugger.logSuccess(`📡 DNAAS topology loaded: ${topologyType} (${editor.objects.length} objects)`);
            }
        }
    },

    /**
     * Enrich termination devices with SSH config from managed devices
     * Extracted from topology.js for modular architecture
     */
    async enrichTerminationDevicesWithManagedConfig(editor, data) {
        if (!data || !data.objects) return data;
        
        try {
            let managedDevices = [];
            if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDevices) {
                try {
                    const result = await ScalerAPI.getDevices();
                    managedDevices = result.devices || [];
                } catch (err) {
                    console.log('[DNAAS] Could not fetch managed devices:', err.message);
                }
            }
            
            if (managedDevices.length === 0) {
                console.log('[DNAAS] No managed devices available for SSH enrichment');
                return data;
            }
            
            const managedByHostname = {};
            const managedByIP = {};
            const managedDevicesList = [];
            managedDevices.forEach(device => {
                if (device.hostname) managedByHostname[device.hostname.toLowerCase()] = device;
                if (device.ip) managedByIP[device.ip] = device;
                if (device.id) managedByHostname[device.id.toLowerCase()] = device;
                managedDevicesList.push(device);
            });
            
            const findManagedDeviceByPartialMatch = (lldpName) => {
                if (!lldpName) return null;
                const nameLower = lldpName.toLowerCase();
                
                for (const managed of managedDevicesList) {
                    const managedHostname = (managed.hostname || '').toLowerCase();
                    const managedId = (managed.id || '').toLowerCase();
                    
                    if (nameLower === managedHostname || nameLower === managedId) return managed;
                    
                    if (managedHostname && managedHostname.length >= 3) {
                        if (nameLower.includes(managedHostname) || nameLower.endsWith(managedHostname) ||
                            nameLower.replace(/[_\-\.]/g, '').includes(managedHostname.replace(/[_\-\.]/g, ''))) {
                            console.log(`[DNAAS] Fuzzy match: "${lldpName}" → "${managed.hostname}"`);
                            return managed;
                        }
                    }
                    
                    if (managedId && managedId.length >= 2) {
                        if (nameLower.includes(managedId) || 
                            nameLower.replace(/[_\-\.]/g, '').includes(managedId.replace(/[_\-\.]/g, ''))) {
                            console.log(`[DNAAS] Fuzzy match by ID: "${lldpName}" → "${managed.id}"`);
                            return managed;
                        }
                    }
                }
                return null;
            };
            
            const dnaasKeywords = ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR', 'AGGREGATION', 'AGG-', 'CORE-'];
            
            data.objects.forEach(obj => {
                if (obj.type !== 'device') return;
                
                const label = (obj.label || '').toUpperCase();
                const isDnaasDevice = dnaasKeywords.some(kw => label.includes(kw));
                if (isDnaasDevice) return;
                
                const labelLower = (obj.label || '').toLowerCase();
                const serial = (obj.deviceSerial || '').toLowerCase();
                const sshHost = obj.sshConfig?.host || obj.sshConfig?.hostBackup || '';
                
                let matchedDevice = null;
                if (labelLower && managedByHostname[labelLower]) matchedDevice = managedByHostname[labelLower];
                else if (serial && managedByHostname[serial]) matchedDevice = managedByHostname[serial];
                else if (sshHost && managedByIP[sshHost]) matchedDevice = managedByIP[sshHost];
                else matchedDevice = findManagedDeviceByPartialMatch(obj.label);
                
                if (matchedDevice) {
                    console.log(`[DNAAS] Enriching termination device "${obj.label}" with managed device SSH config`);
                    obj.sshConfig = obj.sshConfig || {};
                    if (matchedDevice.ip && !obj.sshConfig.host) obj.sshConfig.host = matchedDevice.ip;
                    if (matchedDevice.username) obj.sshConfig.user = matchedDevice.username;
                    if (matchedDevice.password) obj.sshConfig.password = matchedDevice.password;
                    obj.sshConfig.enrichedFromManaged = true;
                    obj.sshConfig.managedDeviceId = matchedDevice.id || matchedDevice.hostname;
                    
                    if (editor.debugger) {
                        editor.debugger.logSuccess(`📡 Termination device "${obj.label}" enriched with SSH from managed device`);
                    }
                }
            });
            
            return data;
        } catch (err) {
            console.warn('[DNAAS] Error enriching termination devices:', err);
            return data;
        }
    },

    /**
     * Save as DNAAS topology with metadata - extracted from topology.js
     */
    saveAsDnaasTopology(editor) {
        const stale = document.getElementById('dnaas-save-dialog');
        if (stale) stale.remove();

        const data = editor.generateTopologyData();
        const deviceCount = editor.objects.filter(o => o.type === 'device').length;
        const linkCount = editor.objects.filter(o => o.type === 'link' || o.type === 'unbound').length;
        
        const promptDialog = document.createElement('div');
        promptDialog.id = 'dnaas-save-dialog';
        promptDialog.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(8px);
            z-index: 10001; display: flex; align-items: center; justify-content: center;
        `;
        
        const isDark = editor.darkMode;
        promptDialog.innerHTML = `
            <div style="
                background: ${isDark ? 'rgba(15, 15, 25, 0.95)' : 'rgba(255, 255, 255, 0.95)'};
                backdrop-filter: blur(24px) saturate(200%);
                border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};
                border-radius: 16px; padding: 24px; min-width: 400px;
                box-shadow: 0 12px 48px rgba(0,0,0,0.3);
            ">
                <h3 style="margin: 0 0 8px 0; color: ${isDark ? '#fff' : '#1a1a1a'}; font-size: 18px;">Save DNAAS Topology</h3>
                <p style="margin: 0 0 16px 0; color: ${isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)'}; font-size: 13px;">
                    ${deviceCount} devices, ${linkCount} links
                </p>
                <input data-role="name" type="text" placeholder="Enter topology name..." style="
                    width: 100%; padding: 10px;
                    border: 1px solid ${isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'};
                    border-radius: 8px; background: ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)'};
                    color: ${isDark ? '#fff' : '#1a1a1a'}; font-size: 14px;
                    margin-bottom: 16px; box-sizing: border-box;
                " />
                <div style="display: flex; gap: 8px; justify-content: flex-end;">
                    <button data-role="cancel" style="
                        padding: 8px 16px; border: 1px solid ${isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'};
                        border-radius: 8px; background: transparent; color: ${isDark ? '#fff' : '#1a1a1a'}; cursor: pointer;
                    ">Cancel</button>
                    <button data-role="save" style="
                        padding: 8px 16px; border: none; border-radius: 8px;
                        background: #FF5E1F; color: #fff; cursor: pointer; font-weight: 600;
                    ">Save</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(promptDialog);
        
        const input = promptDialog.querySelector('[data-role="name"]');
        const saveBtn = promptDialog.querySelector('[data-role="save"]');
        const cancelBtn = promptDialog.querySelector('[data-role="cancel"]');
        
        input.focus();
        
        const doSave = async () => {
            const name = input.value.trim();
            if (!name) { editor.showToast('Please enter a name', 'warning'); return; }
            
            saveBtn.textContent = 'Saving...';
            saveBtn.disabled = true;
            
            data.metadata.isDnaas = true;
            data.metadata.dnaasName = name;
            data.metadata.savedAt = Date.now();
            data.metadata.deviceCount = deviceCount;
            data.metadata.linkCount = linkCount;
            
            try {
                let sectionId = await DnaasHelpers._ensureDnaasSection();
                
                const resp = await fetch(`/api/sections/${sectionId}/save`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, topology: data })
                });
                const result = await resp.json();
                if (result.error) throw new Error(result.error);
                
                promptDialog.remove();
                editor.showToast(`DNAAS topology "${name}" saved`, 'success');
                
                if (editor.loadCustomSections) editor.loadCustomSections();
            } catch (err) {
                saveBtn.textContent = 'Save';
                saveBtn.disabled = false;
                editor.showToast(`Save failed: ${err.message}`, 'error');
            }
        };
        
        saveBtn.onclick = doSave;
        cancelBtn.onclick = () => promptDialog.remove();
        input.onkeydown = (e) => {
            if (e.key === 'Enter') doSave();
            if (e.key === 'Escape') promptDialog.remove();
        };
    },

    /**
     * Correct device credentials - extracted from topology.js
     */
    correctDeviceCredentials(editor) {
        const devices = editor.objects.filter(o => o.type === 'device');
        if (devices.length === 0) return;
        
        let setDefaults = 0;
        
        devices.forEach(device => {
            if (!device.sshConfig) device.sshConfig = {};
            
            if (!device.sshConfig.user && !device.sshConfig.password) {
                const label = (device.label || '').toUpperCase();
                const isDnaasFabric = label.includes('LEAF') || label.includes('SPINE') || 
                                      label.includes('SUPERSPINE') || label.includes('SS-');
                
                if (isDnaasFabric) {
                    device.sshConfig.user = 'sisaev';
                    device.sshConfig.password = 'Drive1234!';
                } else {
                    device.sshConfig.user = 'dnroot';
                    device.sshConfig.password = 'dnroot';
                }
                setDefaults++;
            }
        });
        
        if (setDefaults > 0) {
            console.log(`[Credentials] Set default credentials for ${setDefaults} device(s)`);
        }
    }
};

console.log('[topology-dnaas-helpers.js] DnaasHelpers loaded');
