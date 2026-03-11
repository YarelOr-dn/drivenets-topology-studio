/**
 * SCALER API Client
 * 
 * JavaScript module for communicating with the FastAPI backend.
 * Provides methods for device management, configuration operations,
 * and real-time progress updates via WebSocket.
 * 
 * @version 1.0.0
 * @requires FastAPI backend running on same origin
 */

const ScalerAPI = {
    // Base URL - empty for same origin
    baseUrl: '',
    
    // Active WebSocket connections
    _websockets: {},
    
    // Bridge availability tracking -- prevents console 501 spam
    _bridgeUp: true,
    _bridgeRetryAfter: 0,
    
    // =========================================================================
    // DEVICE OPERATIONS
    // =========================================================================
    
    /**
     * Get list of all registered devices
     * @returns {Promise<{devices: Array, count: number}>}
     */
    async getDevices() {
        const response = await fetch('/api/devices/');
        if (!response.ok) {
            throw new Error(`Failed to fetch devices: ${response.statusText}`);
        }
        return response.json();
    },
    
    /**
     * Get a single device by ID
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Device details
     */
    async getDevice(deviceId) {
        const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}`);
        if (!response.ok) {
            throw new Error(`Device not found: ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Add a new device
     * @param {Object} device - Device configuration
     * @param {string} device.hostname - Device hostname
     * @param {string} device.ip - Device IP address
     * @param {string} device.platform - Platform type (e.g., 'ncp')
     * @param {string} [device.username] - SSH username
     * @param {string} [device.password] - SSH password
     * @returns {Promise<Object>} Created device
     */
    async addDevice(device) {
        const response = await fetch('/api/devices/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(device)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add device');
        }
        return response.json();
    },
    
    /**
     * Update an existing device
     * @param {string} deviceId - Device identifier
     * @param {Object} updates - Fields to update
     * @returns {Promise<Object>} Updated device
     */
    async updateDevice(deviceId, updates) {
        const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update device');
        }
        return response.json();
    },
    
    /**
     * Delete a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Deletion result
     */
    async deleteDevice(deviceId) {
        const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete device');
        }
        return response.json();
    },
    
    /**
     * Get device inventory from CURSOR/device_inventory.json
     * Contains LLDP neighbors and interface details from scaler-monitor
     * @returns {Promise<Object>} Inventory data with devices object
     */
    async getDeviceInventory() {
        try {
            // Try relative path first (same directory as index.html)
            const response = await fetch('device_inventory.json');
            if (!response.ok) {
                throw new Error(`Failed to fetch inventory: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.warn('[ScalerAPI] Failed to load device inventory:', error);
            return { devices: {} };
        }
    },
    
    /**
     * Test SSH connection to a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{status: string, message: string}>}
     */
    async testConnection(deviceId, sshHost = '') {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) {
            try {
                const h = await this.checkHealth();
                if (h?.scaler_bridge?.status === 'ok') {
                    this._bridgeUp = true;
                } else {
                    throw new Error('Config service unavailable. Start the app with ./start.sh or python3 serve.py.');
                }
            } catch (_) {
                throw new Error('Config service unavailable. Start the app with ./start.sh or python3 serve.py.');
            }
        }
        const params = sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : '';
        const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/test${params}`, {
            method: 'POST'
        });
        if (!response.ok) {
            let detail = 'Connection test failed';
            try {
                const err = await response.json();
                detail = err.detail || detail;
                if ((response.status === 501 || response.status === 502 || response.status === 503) &&
                    typeof detail === 'string' && detail.toLowerCase().includes('scaler bridge unavailable')) {
                    this._bridgeUp = false;
                    this._bridgeRetryAfter = Date.now() + 15000;
                }
            } catch (_) {}
            throw new Error(detail);
        }
        this._bridgeUp = true;
        return response.json();
    },
    
    /**
     * Sync (extract) running configuration from device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Sync result with config
     */
    async syncDevice(deviceId) {
        const response = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/sync`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Sync failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // CONFIGURATION OPERATIONS
    // =========================================================================
    
    /**
     * Get running configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{config: string}>}
     */
    async getRunningConfig(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/running`);
        if (!response.ok) {
            throw new Error(`Failed to get running config for ${deviceId}`);
        }
        return response.json();
    },

    /**
     * Sync (fetch and cache) running config from device.
     * @param {string} deviceId - Device identifier
     * @param {string} [sshHost=''] - SSH host override
     * @returns {Promise<{status: string, message: string, lines: number}>}
     */
    async syncConfig(deviceId, sshHost = '') {
        const url = `/api/config/${encodeURIComponent(deviceId)}/sync${sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : ''}`;
        const response = await fetch(url, { method: 'POST' });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Config sync failed');
        }
        return response.json();
    },

    /**
     * Get configuration summary for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Summary with system, interfaces, services, etc.
     */
    async getConfigSummary(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/summary`);
        if (!response.ok) {
            throw new Error(`Failed to get config summary for ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Get unified device context for wizard suggestions (interfaces, LLDP, config summary, free interfaces).
     * @param {string} deviceId - Device identifier
     * @param {boolean} [live=false] - If true, fetch live config from device
     * @returns {Promise<Object>} Device context with interfaces, lldp, config_summary, wan_interfaces, services, etc.
     */
    async getDeviceContext(deviceId, live = false, sshHost = '') {
        const params = new URLSearchParams();
        if (live) params.set('live', 'true');
        if (sshHost) params.set('ssh_host', sshHost);
        const qs = params.toString();
        const url = `/api/devices/${encodeURIComponent(deviceId)}/context${qs ? '?' + qs : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to get device context for ${deviceId}`);
        }
        return response.json();
    },

    /**
     * Get next-wizard suggestions from backend (device_id, completed_wizard, created_data).
     * @param {Object} params - { device_id, completed_wizard, created_data, ssh_host }
     * @returns {Promise<{suggestions: Array}>} Suggestions with wizard, reason, prefill
     */
    async wizardSuggestions(params) {
        const response = await fetch('/api/wizard/suggestions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Wizard suggestions failed');
        }
        return response.json();
    },

    /**
     * Get interfaces configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Array>} List of interface configurations
     */
    async getInterfaces(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/interfaces`);
        if (!response.ok) {
            throw new Error(`Failed to get interfaces for ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Get services configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Services summary
     */
    async getServices(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/services`);
        if (!response.ok) {
            throw new Error(`Failed to get services for ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Get multihoming configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{count: number, interfaces: Object, esi_prefix: string}>}
     */
    async getMultihoming(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/multihoming`);
        if (!response.ok) {
            throw new Error(`Failed to get multihoming for ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Get a specific hierarchy section from config
     * @param {string} deviceId - Device identifier
     * @param {string} hierarchy - Hierarchy name (system, interfaces, services, etc.)
     * @returns {Promise<{config: string}>}
     */
    async getHierarchy(deviceId, hierarchy) {
        const response = await fetch(
            `/api/config/${encodeURIComponent(deviceId)}/hierarchy/${encodeURIComponent(hierarchy)}`
        );
        if (!response.ok) {
            throw new Error(`Failed to get ${hierarchy} for ${deviceId}`);
        }
        return response.json();
    },
    
    // =========================================================================
    // PUSH/DELETE OPERATIONS
    // =========================================================================
    
    /**
     * Validate configuration before pushing
     * @param {Object} request - Validation request
     * @param {string} request.device_id - Target device
     * @param {string} request.config - Configuration to validate
     * @param {string} request.hierarchy - Hierarchy section
     * @returns {Promise<Object>} Validation result
     */
    async validateConfig(request) {
        const response = await fetch('/api/operations/validate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Validation failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // CONFIG GENERATION - Uses SCALER's proper DNOS syntax
    // =========================================================================
    
    /**
     * Generate interface configuration using SCALER's DNOS syntax
     * @param {Object} params - Interface parameters
     * @returns {Promise<{config: string, lines: number, hierarchy: string}>}
     */
    async generateInterfaces(params) {
        const response = await fetch('/api/config/generate/interfaces', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate interfaces');
        }
        return response.json();
    },

    async scanExisting(params) {
        const response = await fetch('/api/config/scan-existing', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Scan failed');
        }
        return response.json();
    },

    async detectPattern(params) {
        const response = await fetch('/api/config/detect-pattern', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Pattern detection failed');
        }
        return response.json();
    },

    async detectL2ACParent(params) {
        const response = await fetch('/api/config/detect/l2ac-parent', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'L2-AC parent detection failed');
        }
        return response.json();
    },

    async detectBGPNeighbors(params) {
        const response = await fetch('/api/config/detect/bgp-neighbors', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'BGP neighbors detection failed');
        }
        return response.json();
    },

    async detectScaleSuggestions(params) {
        const response = await fetch('/api/config/detect/scale-suggestions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Scale suggestions failed');
        }
        return response.json();
    },

    async generateSystem(params) {
        const response = await fetch('/api/config/generate/system', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'System config generation failed');
        }
        return response.json();
    },

    async validatePolicy(params) {
        const response = await fetch('/api/config/validate/policy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Policy validation failed');
        }
        return response.json();
    },

    async generateRoutePolicyStructured(params) {
        const response = await fetch('/api/config/generate/route-policy-structured', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Route policy generation failed');
        }
        return response.json();
    },

    async getSmartDefaults(deviceId, sshHost = '') {
        const url = `/api/config/templates/smart-defaults/${encodeURIComponent(deviceId)}${sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Smart defaults failed');
        }
        return response.json();
    },

    /**
     * Generate service configuration using SCALER's DNOS syntax
     * @param {Object} params - Service parameters
     * @returns {Promise<{config: string, lines: number, hierarchy: string}>}
     */
    async generateServices(params) {
        const response = await fetch('/api/config/generate/services', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate services');
        }
        return response.json();
    },
    async generateBGP(params) {
        const response = await fetch('/api/config/generate/bgp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate BGP');
        }
        return response.json();
    },
    async generateRoutingPolicy(params) {
        const response = await fetch('/api/config/generate/routing-policy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Routing policy generation failed');
        }
        return response.json();
    },
    async generateFlowSpec(params) {
        const response = await fetch('/api/config/generate/flowspec', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'FlowSpec generation failed');
        }
        return response.json();
    },
    async generateIGP(params) {
        const response = await fetch('/api/config/generate/igp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate IGP');
        }
        return response.json();
    },
    async batchGenerate(items) {
        const response = await fetch('/api/config/generate/batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ items })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Batch generation failed');
        }
        return response.json();
    },
    async previewConfigDiff(deviceId, config, sshHost = '') {
        const response = await fetch('/api/config/preview-diff', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ device_id: deviceId, config, ssh_host: sshHost })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Diff preview failed');
        }
        return response.json();
    },
    async mirrorAnalyze(params) {
        const response = await fetch('/api/mirror/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Mirror analyze failed');
        }
        return response.json();
    },
    async mirrorGenerate(params) {
        const response = await fetch('/api/mirror/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Mirror generate failed');
        }
        return response.json();
    },
    async mirrorPreviewDiff(params) {
        const response = await fetch('/api/mirror/preview-diff', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Mirror preview failed');
        }
        return response.json();
    },
    async compareConfigs(deviceIds) {
        const response = await fetch('/api/config/compare', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ device_ids: deviceIds })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Compare failed');
        }
        return response.json();
    },
    async getConfigDiff(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/diff`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Diff failed');
        }
        return response.json();
    },
    async getInterfaces(deviceId) {
        const response = await fetch(`/api/config/${encodeURIComponent(deviceId)}/interfaces`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get interfaces');
        }
        return response.json();
    },
    async getTemplates() {
        const response = await fetch('/api/config/templates');
        if (!response.ok) throw new Error('Failed to get templates');
        return response.json();
    },
    async generateTemplate(templateName, values) {
        const response = await fetch('/api/config/templates/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ template_name: templateName, values: values || {} })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Template generation failed');
        }
        return response.json();
    },
    async discoverDevice(ip) {
        const response = await fetch('/api/devices/discover', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ ip })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Discovery failed');
        }
        return response.json();
    },
    async deleteHierarchyOp(deviceId, hierarchy, dryRun = true) {
        const response = await fetch('/api/operations/delete-hierarchy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ device_id: deviceId, hierarchy, dry_run: dryRun })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }
        return response.json();
    },
    
    /**
     * Push configuration to a device
     * @param {Object} request - Push request
     * @param {string} request.device_id - Target device
     * @param {string} request.config - Configuration to push
     * @param {string} request.hierarchy - Hierarchy section
     * @param {string} request.mode - Push mode ('merge' or 'replace')
     * @param {boolean} [request.dry_run=true] - If true, only validate
     * @returns {Promise<{job_id: string, status: string}>}
     */
    async pushConfig(request) {
        const response = await fetch('/api/operations/push', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Push failed');
        }
        return response.json();
    },

    /**
     * Commit held config on same SSH session (after dry_run push when check passed).
     * @param {string} jobId - Job ID from pushConfig
     * @returns {Promise<{status: string, success: boolean, message: string}>}
     */
    async commitHeldJob(jobId) {
        const response = await fetch(`/api/operations/push/${encodeURIComponent(jobId)}/commit`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Commit failed');
        }
        return response.json();
    },

    /**
     * Cancel held config (discard candidate) and close SSH session.
     * @param {string} jobId - Job ID from pushConfig
     * @returns {Promise<{status: string, success: boolean, message: string}>}
     */
    async cancelHeldJob(jobId) {
        const response = await fetch(`/api/operations/push/${encodeURIComponent(jobId)}/cancel`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cancel failed');
        }
        return response.json();
    },

    /**
     * Cleanup dirty candidate on device after failed commit check.
     * @param {string} jobId - Job ID from pushConfig
     * @returns {Promise<{status: string, success: boolean, message: string}>}
     */
    async cleanupHeldJob(jobId) {
        const response = await fetch(`/api/operations/push/${encodeURIComponent(jobId)}/cleanup`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cleanup failed');
        }
        return response.json();
    },

    async getJobs() {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) return { jobs: [] };
        const response = await fetch('/api/operations/jobs');
        if (!response.ok) {
            if (response.status === 501 || response.status === 502 || response.status === 503) {
                this._bridgeUp = false;
                this._bridgeRetryAfter = Date.now() + 15000;
                return { jobs: [] };
            }
            throw new Error('Failed to fetch jobs');
        }
        this._bridgeUp = true;
        return response.json();
    },

    async getJob(jobId) {
        const response = await fetch(`/api/operations/jobs/${encodeURIComponent(jobId)}`);
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error('Failed to fetch job');
        }
        return response.json();
    },

    async retryJob(jobId) {
        const response = await fetch(`/api/operations/jobs/${encodeURIComponent(jobId)}/retry`, { method: 'POST' });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Retry failed');
        }
        return response.json();
    },

    async deleteJob(jobId) {
        const response = await fetch(`/api/operations/jobs/${encodeURIComponent(jobId)}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete job');
        return response.json();
    },

    /**
     * Get platform limits for a device (max_subifs, etc.)
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{max_subifs: number}>}
     */
    async getLimits(deviceId) {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) return { max_subifs: 20480 };
        const response = await fetch(`/api/config/limits/${encodeURIComponent(deviceId)}`);
        if (!response.ok) {
            if (response.status === 404) {
                return { max_subifs: 20480 };
            }
            if (response.status === 501 || response.status === 502 || response.status === 503) {
                this._bridgeUp = false;
                this._bridgeRetryAfter = Date.now() + 15000;
                return { max_subifs: 20480 };
            }
            throw new Error('Failed to fetch limits');
        }
        this._bridgeUp = true;
        return response.json();
    },
    
    /**
     * Delete a hierarchy section from a device
     * @param {string} deviceId - Target device
     * @param {string} hierarchy - Hierarchy to delete
     * @returns {Promise<{job_id: string, status: string}>}
     */
    async deleteHierarchy(deviceId, hierarchy) {
        const response = await fetch('/api/operations/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                device_id: deviceId,
                hierarchy: hierarchy
            })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }
        return response.json();
    },
    
    /**
     * Sync multihoming between devices
     * @param {Object} request - Sync request
     * @param {Array<string>} request.device_ids - Device IDs to sync
     * @param {number} [request.esi_prefix] - ESI prefix
     * @param {boolean} [request.match_neighbor=true] - Match by neighbor
     * @param {string} [request.redundancy_mode='single-active'] - Redundancy mode
     * @returns {Promise<{job_id: string, status: string}>}
     */
    async syncMultihoming(request) {
        const response = await fetch('/api/operations/multihoming/sync', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Multihoming sync failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // CONFIG GENERATION - Uses SCALER's real generators
    // =========================================================================
    
    /**
     * Generate interface configuration using SCALER CLI syntax
     * @param {Object} params - Interface generation parameters
     * @returns {Promise<{config: string, lines: number}>}
     */
    async generateInterfaces(params) {
        const response = await fetch('/api/config/generate/interfaces', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Interface generation failed');
        }
        return response.json();
    },
    
    /**
     * Generate service configuration using SCALER CLI syntax
     * @param {Object} params - Service generation parameters
     * @returns {Promise<{config: string, lines: number}>}
     */
    async generateServices(params) {
        const response = await fetch('/api/config/generate/services', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Service generation failed');
        }
        return response.json();
    },
    
    /**
     * Compare multihoming configurations between devices
     * @param {Array<string>} deviceIds - Devices to compare
     * @returns {Promise<Object>} Comparison result
     */
    async compareMultihoming(deviceIds) {
        const response = await fetch('/api/operations/multihoming/compare', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({device_ids: deviceIds})
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Comparison failed');
        }
        return response.json();
    },
    
    /**
     * Compare full configurations between two devices
     * @param {Array<string>} deviceIds - Two device IDs to compare
     * @param {string} [hierarchy] - Optional hierarchy to filter (interfaces, services, etc.)
     * @returns {Promise<Object>} Diff result
     */
    async diffConfigs(deviceIds, hierarchy = null) {
        const response = await fetch('/api/operations/diff', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({device_ids: deviceIds, hierarchy: hierarchy})
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Diff failed');
        }
        return response.json();
    },
    
    /**
     * Execute batch operation on multiple devices
     * @param {string} operation - Operation type ('test', 'sync')
     * @param {Array<string>} deviceIds - Devices to operate on
     * @param {Object} [params] - Optional parameters
     * @returns {Promise<{job_id: string}>}
     */
    async batchOperation(operation, deviceIds, params = null) {
        const response = await fetch('/api/operations/batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                operation: operation,
                device_ids: deviceIds,
                params: params
            })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Batch operation failed');
        }
        return response.json();
    },
    
    /**
     * Get status of a running operation
     * @param {string} jobId - Job identifier
     * @returns {Promise<Object>} Job status
     */
    async getOperationStatus(jobId) {
        const response = await fetch(`/api/operations/${encodeURIComponent(jobId)}`);
        if (!response.ok) {
            throw new Error(`Job not found: ${jobId}`);
        }
        return response.json();
    },
    
    /**
     * Cancel a running operation
     * @param {string} jobId - Job identifier
     * @returns {Promise<Object>} Cancellation result
     */
    async cancelOperation(jobId) {
        const response = await fetch(`/api/operations/${encodeURIComponent(jobId)}/cancel`, {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cancel failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // DNAAS DISCOVERY OPERATIONS
    // =========================================================================
    
    /**
     * Start a DNAAS path discovery
     * @param {Object} request - Discovery request
     * @param {string} request.serial1 - First device serial/hostname
     * @param {string} [request.serial2] - Second device serial/hostname
     * @param {boolean} [request.bd_aware=false] - Enable bridge domain discovery
     * @returns {Promise<{job_id: string, message: string}>}
     */
    async startDnaasDiscovery(request) {
        let response;
        try {
            response = await fetch('/api/dnaas/discovery/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(request)
            });
        } catch (fetchErr) {
            if (fetchErr.message && (fetchErr.message.includes('Failed to fetch') || fetchErr.message.includes('NetworkError'))) {
                throw new Error('Discovery API unreachable - check if serve.py and discovery_api.py are running');
            }
            throw fetchErr;
        }
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            const msg = error.error || error.detail || (error.endpoint ? `Endpoint ${error.endpoint} failed` : null) || `HTTP ${response.status}`;
            throw new Error(msg);
        }
        return response.json();
    },
    
    /**
     * Get DNAAS discovery job status
     * @param {string} jobId - Job identifier
     * @returns {Promise<Object>} Discovery status with progress and output
     */
    async getDnaasStatus(jobId) {
        const response = await fetch(`/api/dnaas/discovery/status?job_id=${encodeURIComponent(jobId)}`);
        if (!response.ok) {
            throw new Error(`Discovery job not found: ${jobId}`);
        }
        return response.json();
    },
    
    /**
     * List available DNAAS discovery result files
     * @returns {Promise<{files: Array}>}
     */
    async listDnaasFiles() {
        const response = await fetch('/api/dnaas/discovery/list');
        if (!response.ok) {
            throw new Error('Failed to list discovery files');
        }
        return response.json();
    },
    
    /**
     * Get a specific DNAAS discovery result file
     * @param {string} filename - File name (e.g., dnaas_path_20251230_123456.json)
     * @returns {Promise<Object>} Discovery result data
     */
    async getDnaasFile(filename) {
        const response = await fetch(`/api/dnaas/discovery/file/${encodeURIComponent(filename)}`);
        if (!response.ok) {
            throw new Error(`Discovery file not found: ${filename}`);
        }
        return response.json();
    },
    
    /**
     * Check DNAAS discovery server health
     * @returns {Promise<{status: string, message: string}>}
     */
    async checkDnaasHealth() {
        const response = await fetch('/api/dnaas/discovery/health');
        return response.json();
    },
    
    /**
     * Cancel a running DNAAS discovery job
     * @param {string} jobId - Job identifier to cancel
     * @returns {Promise<{status: string, message: string}>}
     */
    async cancelDnaasDiscovery(jobId) {
        const response = await fetch('/api/dnaas/discovery/cancel', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ job_id: jobId })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cancel failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // MULTI-BD DISCOVERY (Discover ALL Bridge Domains)
    // =========================================================================
    
    /**
     * Start Multi-BD discovery - discovers ALL Bridge Domains from a device
     * @param {Object} request - { serial: string }
     * @returns {Promise<{job_id: string, message: string}>}
     */
    async startMultiBDDiscovery(request) {
        const response = await fetch('/api/dnaas/multi-bd/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Multi-BD discovery start failed');
        }
        return response.json();
    },
    
    /**
     * Get Multi-BD discovery status
     * @param {string} jobId - Job ID from startMultiBDDiscovery
     * @returns {Promise<{status: string, message?: string, bd_count?: number, result_file?: string}>}
     */
    async getMultiBDDiscoveryStatus(jobId) {
        const response = await fetch(`/api/dnaas/multi-bd/status?job_id=${encodeURIComponent(jobId)}`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Multi-BD job not found: ${jobId}`);
        }
        return response.json();
    },
    
    /**
     * Get Multi-BD discovery result file
     * @param {string} filename - Result file name
     * @returns {Promise<Object>} - Topology data with BD metadata
     */
    async getMultiBDFile(filename) {
        const response = await fetch(`/api/dnaas/multi-bd/file/${encodeURIComponent(filename)}`);
        if (!response.ok) {
            throw new Error(`Multi-BD file not found: ${filename}`);
        }
        return response.json();
    },
    
    /**
     * Cancel Multi-BD discovery job
     * @param {string} jobId - Job ID to cancel
     * @returns {Promise<{status: string, message: string}>}
     */
    async cancelMultiBDDiscovery(jobId) {
        const response = await fetch('/api/dnaas/multi-bd/cancel', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ job_id: jobId })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Multi-BD cancel failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // WEBSOCKET FOR REAL-TIME PROGRESS
    // =========================================================================
    
    /**
     * Connect to WebSocket for real-time progress updates
     * @param {string} jobId - Job identifier to track
     * @param {Object} callbacks - Event callbacks
     * @param {Function} [callbacks.onProgress] - Called with (percent, message)
     * @param {Function} [callbacks.onTerminal] - Called with (line)
     * @param {Function} [callbacks.onStep] - Called with (current, total, name)
     * @param {Function} [callbacks.onComplete] - Called with (success, result)
     * @param {Function} [callbacks.onError] - Called with (message)
     * @param {Function} [callbacks.onClose] - Called when connection closes
     * @returns {WebSocket} The WebSocket instance
     */
    /**
     * Connect to push progress via SSE (EventSource). Use for config push jobs.
     * @param {string} jobId - Job identifier from pushConfig
     * @param {Object} callbacks - Same as connectProgress
     * @returns {EventSource} The EventSource instance
     */
    connectPushProgress(jobId, callbacks) {
        const url = (this.baseUrl || '') + `/api/config/push/progress/${encodeURIComponent(jobId)}`;
        const es = new EventSource(url || `/api/config/push/progress/${encodeURIComponent(jobId)}`);
        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const terminal = data.terminal || [];
                if (Array.isArray(terminal) && terminal.length && callbacks.onTerminal) {
                    terminal.forEach((chunk) => callbacks.onTerminal(chunk));
                }
                if (data.done) {
                    es.close();
                    callbacks.onProgress?.(data.success ? 100 : 0, data.message);
                    callbacks.onComplete?.(data.success, { message: data.message, terminal_full: data.terminal_full, cancelled: data.cancelled });
                } else if (data.awaiting_decision || data.status === 'awaiting_decision') {
                    callbacks.onAwaitingDecision?.(data);
                } else {
                    const pct = data.percent || 0;
                    callbacks.onProgress?.(pct, data.message || data.phase);
                }
            } catch (e) {
                console.error('[ScalerAPI] Failed to parse SSE message:', e);
            }
        };
        es.onerror = () => {
            es.close();
            callbacks.onError?.('Progress stream error');
        };
        return es;
    },

    connectProgress(jobId, callbacks) {
        // Prefer SSE for push jobs (scaler_bridge implements push progress via SSE)
        if (typeof EventSource !== 'undefined') {
            return this.connectPushProgress(jobId, callbacks);
        }
        // Fallback: WebSocket (if serve.py ever adds WS support)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/progress/${jobId}`;
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log(`[ScalerAPI] WebSocket connected for job ${jobId}`);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'progress':
                        callbacks.onProgress?.(data.percent, data.message);
                        break;
                    case 'terminal':
                        callbacks.onTerminal?.(data.line);
                        break;
                    case 'step':
                        callbacks.onStep?.(data.current, data.total, data.name);
                        break;
                    case 'complete':
                        callbacks.onComplete?.(data.success, data.result);
                        break;
                    case 'error':
                        callbacks.onError?.(data.message);
                        break;
                    default:
                        console.log(`[ScalerAPI] Unknown message type: ${data.type}`, data);
                }
            } catch (e) {
                console.error('[ScalerAPI] Failed to parse WebSocket message:', e);
            }
        };
        
        ws.onerror = (error) => {
            console.error(`[ScalerAPI] WebSocket error for job ${jobId}:`, error);
            callbacks.onError?.('WebSocket connection error');
        };
        
        ws.onclose = (event) => {
            console.log(`[ScalerAPI] WebSocket closed for job ${jobId}:`, event.code, event.reason);
            delete this._websockets[jobId];
            callbacks.onClose?.();
        };
        
        // Store reference
        this._websockets[jobId] = ws;
        
        return ws;
    },
    
    /**
     * Disconnect WebSocket for a specific job
     * @param {string} jobId - Job identifier
     */
    disconnectProgress(jobId) {
        const ws = this._websockets[jobId];
        if (ws) {
            ws.close();
            delete this._websockets[jobId];
        }
    },
    
    /**
     * Disconnect all active WebSocket connections
     */
    disconnectAll() {
        Object.keys(this._websockets).forEach(jobId => {
            this._websockets[jobId].close();
        });
        this._websockets = {};
    },
    
    // =========================================================================
    // HEALTH CHECK
    // =========================================================================
    
    /**
     * Check API server health
     * @returns {Promise<{status: string, service: string, version: string}>}
     */
    async checkHealth() {
        const response = await fetch('/api/health');
        if (!response.ok) {
            throw new Error('API server is not healthy');
        }
        const data = await response.json();
        if (data?.scaler_bridge?.status === 'ok') {
            this._bridgeUp = true;
        }
        return data;
    },
    
    // =========================================================================
    // UTILITY METHODS
    // =========================================================================
    
    /**
     * Poll for operation status until complete
     * @param {string} jobId - Job identifier
     * @param {Object} callbacks - Progress callbacks
     * @param {number} [interval=1000] - Polling interval in ms
     * @returns {Promise<Object>} Final result
     */
    async pollUntilComplete(jobId, callbacks, interval = 1000) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getOperationStatus(jobId);
                    
                    if (status.progress !== undefined) {
                        callbacks.onProgress?.(status.progress, status.message);
                    }
                    
                    if (status.status === 'completed') {
                        callbacks.onComplete?.(true, status.result);
                        resolve(status);
                    } else if (status.status === 'failed' || status.status === 'error') {
                        callbacks.onError?.(status.error || 'Operation failed');
                        reject(new Error(status.error || 'Operation failed'));
                    } else {
                        // Still running, poll again
                        setTimeout(poll, interval);
                    }
                } catch (e) {
                    callbacks.onError?.(e.message);
                    reject(e);
                }
            };
            
            poll();
        });
    },

    // =====================================================================
    // Image Upgrade - Jenkins Build Browsing
    // =====================================================================

    async getBuildsForBranch(branch, opts = {}) {
        const resp = await fetch('/api/operations/image-upgrade/builds', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branch, ...opts }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to fetch builds (${resp.status})`);
        }
        return resp.json();
    },

    async resolveJenkinsUrl(url) {
        const resp = await fetch('/api/operations/image-upgrade/resolve-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to resolve URL (${resp.status})`);
        }
        return resp.json();
    },

    async getBuildStack(branch, buildNumber) {
        const resp = await fetch('/api/operations/image-upgrade/stack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branch, build_number: buildNumber }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get stack (${resp.status})`);
        }
        return resp.json();
    },
};

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScalerAPI;
}

console.log('[ScalerAPI] Loaded - API client ready');

