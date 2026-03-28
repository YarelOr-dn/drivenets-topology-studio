/**
 * SCALER API Client
 * 
 * JavaScript module for communicating with the FastAPI backend.
 * Provides methods for device management, configuration operations,
 * and real-time progress updates via WebSocket.
 * 
 * @version 1.0.0
 * @requires FastAPI backend running on same origin
 *
 * Domain sections in this file (search for "// ====="):
 *   Core helpers | Devices + SSH/console | Config read/write |
 *   Config generation | Push/operations | DNAAS | Multi-BD | Progress SSE/WS |
 *   Health | Image upgrade (Jenkins)
 */

const ScalerAPI = {
    // Base URL - empty for same origin
    baseUrl: '',
    
    // Active WebSocket connections
    _websockets: {},
    
    // Bridge availability tracking -- prevents console 501 spam
    _bridgeUp: true,
    _bridgeRetryAfter: 0,

    /**
     * Resolve API path to full URL (prepends baseUrl for remote server access).
     */
    _api(path) {
        return (this.baseUrl || '') + path;
    },

    /**
     * WebSocket origin for scaler bridge (in-browser terminal, etc.).
     * When baseUrl is set (e.g. http://lab:8766), uses that host and port with ws/wss.
     * When empty (same-origin HTTP via serve.py proxy), uses page hostname and port 8766.
     * @returns {string} e.g. ws://localhost:8766 or wss://host:8766
     */
    getBridgeWebSocketOrigin() {
        const locProto = (typeof window !== 'undefined' && window.location && window.location.protocol === 'https:')
            ? 'wss:' : 'ws:';
        const base = (this.baseUrl || '').trim();
        if (base) {
            try {
                const u = new URL(base, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
                const wsProto = u.protocol === 'https:' ? 'wss:' : 'ws:';
                const portPart = u.port ? `:${u.port}` : '';
                return `${wsProto}//${u.hostname}${portPart}`;
            } catch (e) {
                console.warn('[ScalerAPI] getBridgeWebSocketOrigin: invalid baseUrl, fallback', e);
            }
        }
        if (typeof window === 'undefined' || !window.location) {
            return 'ws://localhost:8766';
        }
        return `${locProto}//${window.location.hostname}:8766`;
    },

    _formatError(detail, fallback) {
        if (!detail) return fallback || 'Request failed';
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            return detail.map(d => {
                if (typeof d === 'string') return d;
                const loc = (d.loc || []).join(' > ');
                return loc ? `${loc}: ${d.msg || d.message || ''}` : (d.msg || d.message || JSON.stringify(d));
            }).join('; ');
        }
        return String(detail);
    },

    /**
     * Fetch with timeout using AbortController. Rejects if response takes
     * longer than timeoutMs. Caller's signal (if any) is also respected.
     */
    _fetchWithTimeout(url, opts = {}, timeoutMs = 15000) {
        const controller = new AbortController();
        const externalSignal = opts.signal;
        if (externalSignal?.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'));
        if (externalSignal) {
            externalSignal.addEventListener('abort', () => controller.abort(), { once: true });
        }
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        return fetch(url, { ...opts, signal: controller.signal })
            .finally(() => clearTimeout(timer));
    },

    // =========================================================================
    // CORE (_api, WebSocket origin, errors, fetch timeout)
    // =========================================================================
    
    // =========================================================================
    // DEVICE REGISTRY (GET/POST/PUT/DELETE /api/devices/* where applicable)
    // =========================================================================
    
    /**
     * Get list of all registered devices
     * @returns {Promise<{devices: Array, count: number}>}
     */
    async getDevices() {
        const response = await fetch(this._api('/api/devices/'));
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
        const response = await fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}`));
        if (!response.ok) {
            throw new Error(`Device not found: ${deviceId}`);
        }
        return response.json();
    },
    
    // =========================================================================
    // SSH / CONSOLE / PDU / TERMINAL (scaler_bridge /api/ssh/*, WebSocket terminal)
    // =========================================================================
    
    /**
     * Probe connection methods for a device (TCP reachability check).
     * @param {string} deviceId - Device identifier
     * @param {string} [sshHost] - SSH host/IP from canvas
     * @returns {Promise<{methods: Array, recommended: string, device_state: string}>}
     */
    async probeConnection(deviceId, sshHost = '') {
        const response = await fetch(this._api('/api/ssh/probe'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, ssh_host: sshHost || '' })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `Probe failed (HTTP ${response.status})` }));
            throw new Error(err.detail || 'Probe failed');
        }
        return response.json();
    },

    /**
     * Quick TCP check (e.g. port 22 on NCC management IP before iTerm).
     * @param {string} host - IPv4
     * @param {number} [port=22]
     */
    async checkPort(host, port = 22) {
        const q = `?host=${encodeURIComponent(host)}&port=${encodeURIComponent(port)}`;
        const response = await fetch(this._api('/api/ssh/check-port' + q));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'check-port failed');
        }
        return response.json();
    },

    /**
     * Background: virsh console to NCC, show interfaces management, verify SSH; updates operational.json if ok.
     * @param {Object} p
     * @param {string} p.deviceId
     * @param {string} p.kvmHost
     * @param {string} [p.kvmUser]
     * @param {string} p.kvmPass
     * @param {string[]} [p.nccVms]
     * @param {string} [p.activeNcc]
     */
    async discoverNccMgmtIp({ deviceId, kvmHost, kvmUser, kvmPass, nccVms, activeNcc }) {
        const response = await fetch(this._api('/api/ssh/discover-ncc-mgmt'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId,
                kvm_host: kvmHost,
                kvm_user: kvmUser || 'dn',
                kvm_pass: kvmPass,
                ncc_vms: nccVms || [],
                active_ncc: activeNcc || ''
            })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'NCC mgmt discovery failed');
        }
        return response.json();
    },
    
    /**
     * Discover console path via Zohar's DB (primary) or Device42 (fallback).
     * @param {string} deviceId - Device identifier
     * @param {string} [serialNumber] - Serial number (optional)
     * @param {string} [sshHost] - SSH host (optional)
     * @returns {Promise<{console_server, port, source, pdu_entries, serial_no}>}
     */
    async discoverConsole(deviceId, serialNumber = '', sshHost = '') {
        const response = await fetch(this._api('/api/ssh/discover-console'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, serial_number: serialNumber, ssh_host: sshHost })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Console discovery failed');
        }
        return response.json();
    },

    /**
     * PDU power action (reboot / off / on / status) via Zohar's PDU mapping.
     * @param {Object} opts - { serial_number?, device_id?, action: reboot|off|on|status, pdu_host?, outlet? }
     * @returns {Promise<{success, status_output, pdu_host, outlet, cli_type}>}
     */
    async pduPower(opts) {
        const response = await fetch(this._api('/api/ssh/pdu-power'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(opts)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'PDU action failed');
        }
        return response.json();
    },

    /**
     * Scan console server ports to find a device by hostname.
     * Probes each port on known ATEN console servers, looking for a prompt match.
     * @param {string} deviceId
     * @param {string} [serialNumber]
     * @param {string} [consoleServer] - optional hint (e.g. "console-b15")
     * @returns {Promise<{found, console_server, console_host, port, scanned, all_results}>}
     */
    async consoleScan(deviceId, serialNumber = '', consoleServer = '') {
        const response = await fetch(this._api('/api/ssh/console-scan'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId,
                serial_number: serialNumber,
                console_server: consoleServer
            })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Console scan failed');
        }
        return response.json();
    },

    /**
     * Open in-browser WebSocket terminal to device
     * @param {Object} opts - { deviceId, host, user, password, method, deviceLabel }
     */
    openTerminal(opts) {
        if (typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
            window.TerminalPanel.open(opts);
        } else {
            console.warn('[ScalerAPI] TerminalPanel not available');
        }
    },
    
    // =========================================================================
    // DEVICE MUTATIONS (add/update/delete inventory, static JSON)
    // =========================================================================
    
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
        const response = await fetch(this._api('/api/devices/'), {
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
        const response = await fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}`), {
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
        const response = await fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}`), {
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
        const response = await fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/test${params}`), {
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
        const response = await fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/sync`), {
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
        const response = await fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/running`));
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
        const url = this._api(`/api/config/${encodeURIComponent(deviceId)}/sync${sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : ''}`);
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
        const response = await fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/summary`));
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
        const url = this._api(`/api/devices/${encodeURIComponent(deviceId)}/context${qs ? '?' + qs : ''}`);
        const timeout = live ? 30000 : 8000;
        const response = await this._fetchWithTimeout(url, {}, timeout);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Failed to get device context for ${deviceId}`);
        }
        return response.json();
    },

    /**
     * Get git_commit only (lightweight SSH). Use when context returns null git_commit.
     * @param {string} deviceId - Device identifier
     * @param {string} [sshHost] - SSH IP/hostname from canvas device
     * @param {string} [sshUser] - SSH username (falls back to global default)
     * @param {string} [sshPassword] - SSH password (falls back to global default)
     * @returns {Promise<{git_commit: string|null}>}
     */
    async getDeviceGitCommit(deviceId, sshHost = '', sshUser = '', sshPassword = '') {
        const params = new URLSearchParams();
        if (sshHost) params.set('ssh_host', sshHost);
        if (sshUser) params.set('ssh_user', sshUser);
        if (sshPassword) params.set('ssh_password', sshPassword);
        const qs = params.toString();
        const url = this._api(`/api/devices/${encodeURIComponent(deviceId)}/git-commit${qs ? '?' + qs : ''}`);
        const response = await this._fetchWithTimeout(url, {}, 20000);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Failed to get git_commit for ${deviceId}`);
        }
        return response.json();
    },

    /**
     * Get next-wizard suggestions from backend (device_id, completed_wizard, created_data).
     * @param {Object} params - { device_id, completed_wizard, created_data, ssh_host }
     * @returns {Promise<{suggestions: Array}>} Suggestions with wizard, reason, prefill
     */
    async wizardSuggestions(params) {
        const response = await fetch(this._api('/api/wizard/suggestions'), {
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
        const response = await fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/interfaces`));
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
        const response = await fetch(this._api('/api/operations/validate'), {
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
        const response = await fetch(this._api('/api/config/generate/interfaces'), {
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

    async saveConfigForLater(deviceId, config) {
        const response = await fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/save`), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ config })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save config');
        }
        return response.json();
    },

    async generateUndo(params) {
        const response = await fetch(this._api('/api/config/generate/undo'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate undo config');
        }
        return response.json();
    },

    async scanExisting(params) {
        const response = await fetch(this._api('/api/config/scan-existing'), {
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

    async scanIPs(params) {
        const response = await fetch(this._api('/api/config/scan-ips'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'IP scan failed');
        }
        return response.json();
    },

    async detectPattern(params) {
        const response = await fetch(this._api('/api/config/detect-pattern'), {
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
        const response = await fetch(this._api('/api/config/detect/l2ac-parent'), {
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
        const response = await fetch(this._api('/api/config/detect/bgp-neighbors'), {
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

    async getMenuSummary(deviceIds = []) {
        const ids = Array.isArray(deviceIds) ? deviceIds : [];
        const qs = ids.length ? '?device_ids=' + encodeURIComponent(ids.join(',')) : '';
        const response = await fetch(this._api('/api/config/menu-summary' + qs));
        if (!response.ok) return { devices: 0, interfaces: { phys: 0, bundle: 0, subif: 0 }, services: { fxc: 0, l2vpn: 0, evpn: 0, vpws: 0, vrf: 0 }, lldp_total: 0 };
        return response.json();
    },

    async detectScaleSuggestions(params) {
        const response = await fetch(this._api('/api/config/detect/scale-suggestions'), {
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
        const response = await fetch(this._api('/api/config/generate/system'), {
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
        const response = await fetch(this._api('/api/config/validate/policy'), {
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
        const response = await fetch(this._api('/api/config/generate/route-policy-structured'), {
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
        const url = this._api(`/api/config/templates/smart-defaults/${encodeURIComponent(deviceId)}${sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : ''}`);
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
        const response = await fetch(this._api('/api/config/generate/services'), {
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
        const response = await fetch(this._api('/api/config/generate/bgp'), {
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
        const response = await fetch(this._api('/api/config/generate/routing-policy'), {
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
        const response = await fetch(this._api('/api/config/generate/flowspec'), {
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
    async flowspecDependencyCheck(params) {
        const response = await fetch(this._api('/api/config/flowspec-dependency-check'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'FlowSpec dependency check failed');
        }
        return response.json();
    },
    async generateIGP(params) {
        const response = await fetch(this._api('/api/config/generate/igp'), {
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
        const response = await fetch(this._api('/api/config/generate/batch'), {
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
        const response = await fetch(this._api('/api/config/preview-diff'), {
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
        const response = await fetch(this._api('/api/mirror/analyze'), {
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
        const response = await fetch(this._api('/api/mirror/generate'), {
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
        const response = await fetch(this._api('/api/mirror/preview-diff'), {
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
        const response = await fetch(this._api('/api/config/compare'), {
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
        const response = await fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/diff`));
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Diff failed');
        }
        return response.json();
    },
    async getTemplates() {
        const response = await fetch(this._api('/api/config/templates'));
        if (!response.ok) throw new Error('Failed to get templates');
        return response.json();
    },
    async generateTemplate(templateName, values) {
        const response = await fetch(this._api('/api/config/templates/generate'), {
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
        const response = await fetch(this._api('/api/devices/discover'), {
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
    async getDeleteHierarchyOptions() {
        const response = await fetch(this._api('/api/config/delete-hierarchy-options'));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to load hierarchy options');
        }
        return response.json();
    },
    async deleteHierarchyOp(deviceId, hierarchy, dryRun = true, subPath = '') {
        const body = { device_id: deviceId, hierarchy, dry_run: dryRun };
        if (subPath && subPath.trim()) body.sub_path = subPath.trim();
        const response = await fetch(this._api('/api/operations/delete-hierarchy'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
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
    async setHostname(deviceId, hostname, sshHost) {
        const response = await fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/set-hostname`), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ hostname, ssh_host: sshHost || '' })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Hostname change failed');
        }
        return response.json();
    },

    /**
     * Toggle SSH connection pool on/off for faster operations.
     * @param {boolean} enabled - true to enable pool, false to disable
     * @returns {Promise<{enabled: boolean, count: number}>}
     */
    async toggleSSHPool(enabled) {
        const response = await fetch(this._api('/api/ssh-pool/toggle'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ enabled: !!enabled })
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'SSH pool toggle failed');
        }
        return response.json();
    },

    /**
     * Get SSH pool status: enabled, count, per-device connection state.
     * @returns {Promise<{enabled: boolean, count: number, entries: Array}>}
     */
    async getSSHPoolStatus() {
        const response = await fetch(this._api('/api/ssh-pool/status'));
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'SSH pool status failed');
        }
        return response.json();
    },

    /**
     * Evict (force-close) pooled SSH client(s) for a device.
     * Call when device is deleted or credentials changed.
     * @param {string} ip - Canvas SSH host (IPv4, hostname, or serial)
     * @param {string} [deviceId] - Device label for resolving serial/hostname to mgmt IP
     * @returns {Promise<{status: string, evicted: string, evicted_keys?: string[]}>}
     */
    async evictSSHPoolConnection(ip, deviceId = '') {
        const body = { ip: ip || '' };
        if (deviceId) {
            body.device_id = deviceId;
        }
        const response = await fetch(this._api('/api/ssh-pool/evict'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'SSH pool evict failed');
        }
        return response.json();
    },

    async getPushEstimate(params) {
        const response = await fetch(this._api('/api/config/push/estimate'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Estimate failed');
        }
        return response.json();
    },

    async pushConfig(request) {
        const body = {
            ...request,
            push_method: request.push_method || 'terminal_paste',
            load_mode: request.load_mode || 'merge',
        };
        const response = await fetch(this._api('/api/operations/push'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
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
        const response = await fetch(this._api(`/api/operations/push/${encodeURIComponent(jobId)}/commit`), {
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
        const response = await fetch(this._api(`/api/operations/push/${encodeURIComponent(jobId)}/cancel`), {
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
        const response = await fetch(this._api(`/api/operations/push/${encodeURIComponent(jobId)}/cleanup`), {
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
        try {
            const response = await fetch(this._api('/api/operations/jobs'));
            if (!response.ok) {
                if (response.status === 501 || response.status === 502 || response.status === 503 || response.status === 500) {
                    this._bridgeUp = false;
                    this._bridgeRetryAfter = Date.now() + 15000;
                    return { jobs: [] };
                }
                throw new Error('Failed to fetch jobs');
            }
            this._bridgeUp = true;
            return response.json();
        } catch (e) {
            this._bridgeUp = false;
            this._bridgeRetryAfter = Date.now() + 10000;
            return { jobs: [] };
        }
    },

    async getJob(jobId) {
        const response = await fetch(this._api(`/api/operations/jobs/${encodeURIComponent(jobId)}`));
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error('Failed to fetch job');
        }
        return response.json();
    },

    async retryJob(jobId) {
        const response = await fetch(this._api(`/api/operations/jobs/${encodeURIComponent(jobId)}/retry`), { method: 'POST' });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Retry failed');
        }
        return response.json();
    },

    async deleteJob(jobId) {
        const response = await fetch(this._api(`/api/operations/jobs/${encodeURIComponent(jobId)}`), { method: 'DELETE' });
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
        const response = await fetch(this._api(`/api/config/limits/${encodeURIComponent(deviceId)}`));
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
        return this.deleteHierarchyOp(deviceId, hierarchy, false);
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
        const response = await fetch(this._api('/api/operations/multihoming/sync'), {
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
    
    /**
     * Compare multihoming configurations between devices
     * @param {Array<string>} deviceIds - Devices to compare
     * @returns {Promise<Object>} Comparison result
     */
    async compareMultihoming(deviceIds) {
        const response = await fetch(this._api('/api/operations/multihoming/compare'), {
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
    /**
     * Cancel a running operation
     * @param {string} jobId - Job identifier
     * @returns {Promise<Object>} Cancellation result
     */
    async cancelOperation(jobId) {
        const response = await fetch(this._api(`/api/operations/${encodeURIComponent(jobId)}/cancel`), {
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
            response = await fetch(this._api('/api/dnaas/discovery/start'), {
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
        const response = await fetch(this._api(`/api/dnaas/discovery/status?job_id=${encodeURIComponent(jobId)}`));
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
        const response = await fetch(this._api('/api/dnaas/discovery/list'));
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
        const response = await fetch(this._api(`/api/dnaas/discovery/file/${encodeURIComponent(filename)}`));
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
        const response = await fetch(this._api('/api/dnaas/discovery/health'));
        return response.json();
    },
    
    /**
     * Cancel a running DNAAS discovery job
     * @param {string} jobId - Job identifier to cancel
     * @returns {Promise<{status: string, message: string}>}
     */
    async cancelDnaasDiscovery(jobId) {
        const response = await fetch(this._api('/api/dnaas/discovery/cancel'), {
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
        const response = await fetch(this._api('/api/dnaas/multi-bd/start'), {
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
        const response = await fetch(this._api(`/api/dnaas/multi-bd/status?job_id=${encodeURIComponent(jobId)}`));
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
        const response = await fetch(this._api(`/api/dnaas/multi-bd/file/${encodeURIComponent(filename)}`));
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
        const response = await fetch(this._api('/api/dnaas/multi-bd/cancel'), {
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
    connectPushProgress(jobId, callbacks, options) {
        const url = this._api(`/api/config/push/progress/${encodeURIComponent(jobId)}`);
        let retryCount = 0;
        const MAX_RETRIES = 5;
        let done = false;
        let currentEs = null;
        let heartbeatTimer = null;
        const HEARTBEAT_TIMEOUT = 30000;
        let _terminalLinesSent = (options && options.terminalOffset) || 0;

        const connect = () => {
            const es = new EventSource(url);
            currentEs = es;

            const resetHeartbeat = () => {
                if (heartbeatTimer) clearTimeout(heartbeatTimer);
                heartbeatTimer = setTimeout(() => {
                    if (done) return;
                    console.warn('[ScalerAPI] No SSE data for 30s -- reconnecting');
                    es.close();
                    scheduleReconnect();
                }, HEARTBEAT_TIMEOUT);
            };

            const scheduleReconnect = () => {
                if (done || retryCount >= MAX_RETRIES) {
                    if (!done) callbacks.onError?.('Connection lost after ' + MAX_RETRIES + ' retries. The operation may still be running.');
                    return;
                }
                retryCount++;
                const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 10000);
                console.log(`[ScalerAPI] SSE reconnect attempt ${retryCount}/${MAX_RETRIES} in ${delay}ms`);
                setTimeout(() => { if (!done) connect(); }, delay);
            };

            resetHeartbeat();
            es.onmessage = (event) => {
                resetHeartbeat();
                retryCount = 0;
                try {
                    const data = JSON.parse(event.data);
                    const terminal = data.terminal || [];
                    const terminalFull = data.terminal_full || [];
                    if (Array.isArray(terminal) && terminal.length && callbacks.onTerminal) {
                        const fullCount = terminalFull.length || (_terminalLinesSent + terminal.length);
                        if (_terminalLinesSent > 0 && terminal.length === fullCount) {
                            const newOnly = terminalFull.slice(_terminalLinesSent);
                            newOnly.forEach((chunk) => callbacks.onTerminal(chunk));
                            _terminalLinesSent = fullCount;
                        } else {
                            terminal.forEach((chunk) => callbacks.onTerminal(chunk));
                            _terminalLinesSent += terminal.length;
                        }
                    }
                    if (data.done) {
                        done = true;
                        if (heartbeatTimer) clearTimeout(heartbeatTimer);
                        es.close();
                        callbacks.onProgress?.(data.success ? 100 : 0, data.message, {
                            elapsed_seconds: data.elapsed_seconds,
                            estimated_remaining_seconds: 0,
                        });
                        if (data.device_state && typeof callbacks.onDeviceState === 'function') {
                            callbacks.onDeviceState(data.device_state);
                        }
                        callbacks.onComplete?.(data.success, { message: data.message, terminal_full: data.terminal_full, cancelled: data.cancelled, device_state: data.device_state });
                    } else if (data.awaiting_decision || data.status === 'awaiting_decision') {
                        callbacks.onAwaitingDecision?.(data);
                    } else {
                        const pct = data.percent || 0;
                        callbacks.onProgress?.(pct, data.message || data.phase, {
                            elapsed_seconds: data.elapsed_seconds,
                            estimated_remaining_seconds: data.estimated_remaining_seconds,
                        });
                        if (data.device_state && typeof callbacks.onDeviceState === 'function') {
                            callbacks.onDeviceState(data.device_state);
                        }
                    }
                } catch (e) {
                    console.error('[ScalerAPI] Failed to parse SSE message:', e);
                }
            };
            es.onerror = () => {
                if (heartbeatTimer) clearTimeout(heartbeatTimer);
                es.close();
                if (!done) scheduleReconnect();
            };
        };

        connect();
        return { close: () => { done = true; if (heartbeatTimer) clearTimeout(heartbeatTimer); currentEs?.close(); } };
    },

    connectProgress(jobId, callbacks, options) {
        if (typeof EventSource !== 'undefined') {
            return this.connectPushProgress(jobId, callbacks, options);
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
        const response = await fetch(this._api('/api/health'));
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

    // =========================================================================
    // IMAGE UPGRADE / JENKINS (/api/operations/image-upgrade/*)
    // =========================================================================

    async getBuildsForBranch(branch, opts = {}) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/builds'), {
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
        const resp = await fetch(this._api('/api/operations/image-upgrade/resolve-url'), {
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
        const resp = await fetch(this._api('/api/operations/image-upgrade/stack'), {
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

    async listBranches(type = 'dev') {
        const resp = await fetch(this._api('/api/operations/image-upgrade/branches'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to list branches (${resp.status})`);
        }
        return resp.json();
    },

    async getBranchSummaries(branches) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/branch-summaries'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branches }),
        });
        if (!resp.ok) return {};
        const data = await resp.json();
        return data.summaries || {};
    },

    async detectBranchSwitch(params) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/branch-switch'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to detect branch switch (${resp.status})`);
        }
        return resp.json();
    },

    async checkVersionCompat(params) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/compat'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to check version compat (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradePlan(params) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/plan'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get upgrade plan (${resp.status})`);
        }
        return resp.json();
    },

    async triggerUpgradeBuild(branch, opts = {}) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/trigger-build'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                branch,
                with_baseos: opts.with_baseos !== false,
                qa_version: opts.qa_version || false,
                with_sanitizer: opts.with_sanitizer || false,
                auto_push: opts.auto_push || false,
                device_ids: opts.device_ids || [],
                ssh_hosts: opts.ssh_hosts || {},
                components: opts.components || ['DNOS', 'GI', 'BaseOS'],
            }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to trigger build (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeBuildStatus(jobId, latest = false) {
        const qs = latest ? '?latest=true' : '';
        const resp = await fetch(this._api(`/api/operations/image-upgrade/build-status/${encodeURIComponent(jobId)}${qs}`));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get build status (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeBuildLog(branch, buildNumber) {
        const qs = buildNumber ? `?build_number=${buildNumber}` : '';
        const resp = await fetch(this._api(`/api/operations/image-upgrade/build-log/${encodeURIComponent(branch)}${qs}`));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get build log (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeDeviceStatus(deviceIds, sshHosts = {}, cachedOnly = false) {
        const ids = Array.isArray(deviceIds) ? deviceIds.join(',') : String(deviceIds || '');
        const hosts = Array.isArray(deviceIds) ? deviceIds.map(id => sshHosts[id] || '').join(',') : '';
        const qs = new URLSearchParams({ device_ids: ids });
        if (hosts) qs.set('ssh_hosts', hosts);
        if (cachedOnly) qs.set('cached_only', 'true');
        const timeout = cachedOnly ? 5000 : 30000;
        const resp = await this._fetchWithTimeout(this._api(`/api/operations/image-upgrade/device-status?${qs}`), {}, timeout);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get device status (${resp.status})`);
        }
        return resp.json();
    },

    async upgradeFromUrls(body) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/from-urls'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to upgrade from URLs (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeRecentSources() {
        const resp = await fetch(this._api('/api/operations/image-upgrade/recent-sources'));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get recent sources (${resp.status})`);
        }
        return resp.json();
    },

    async verifyUpgradeStacks(deviceIds, sshHosts = {}) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/verify-stacks'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_ids: deviceIds, ssh_hosts: sshHosts }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to verify stacks (${resp.status})`);
        }
        return resp.json();
    },

    async restoreUpgradeConfig(deviceIds, sshHosts = {}) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/restore-config'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_ids: deviceIds, ssh_hosts: sshHosts }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to restore config (${resp.status})`);
        }
        return resp.json();
    },

    async waitAndUpgrade(params) {
        const resp = await fetch(this._api('/api/operations/image-upgrade/wait-and-upgrade'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to start wait-and-upgrade (${resp.status})`);
        }
        return resp.json();
    },
};

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScalerAPI;
}

console.log('[ScalerAPI] Loaded - API client ready');

