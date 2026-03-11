// ============================================================================
// TOPOLOGY NETWORK MAPPER MODULE
// ============================================================================
// Recursive LLDP-based network discovery with auto-layout topology generation.
//
// Features:
//   - Discover network via BFS LLDP crawl from seed device(s)
//   - Support for single/multi seed, device inventory, Network Mapper MCP
//   - Live progress with device count, log stream, progress bar
//   - Force-directed auto-layout for up to 100 devices
//   - Save to dedicated "Network Mapper" topology domain
//
// Usage:
//   const nm = new NetworkMapperManager(editor);
//   nm.setupPanel();
// ============================================================================

class NetworkMapperManager {
    constructor(editor) {
        this.editor = editor;
        this._jobId = null;
        this._pollInterval = null;
        this._lastDiscoveryData = null;
        this._pollFailureCount = 0;
    }

    // ========== PANEL SETUP ==========

    setupPanel() {
        const btn = document.getElementById('btn-network-mapper');
        const panel = document.getElementById('network-mapper-panel');
        if (!btn || !panel) {
            console.warn('[NetworkMapper] Panel elements not found');
            return;
        }

        // Move panel to body so it escapes .top-bar's transform containing block
        // (transform: translateZ(0) breaks position:fixed for children)
        document.body.appendChild(panel);

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = panel.style.display === 'block';
            if (!isVisible) {
                // Close other panels
                this._closeOtherPanels();
                this._positionPanel(btn, panel);
                panel.style.display = 'block';
                btn.classList.add('nm-panel-open');
                this.populateSuggestions();
            } else {
                panel.style.display = 'none';
                btn.classList.remove('nm-panel-open');
            }
        });

        // Outside click to close
        document.addEventListener('click', (e) => {
            if (panel.style.display === 'block' && !panel.contains(e.target) && !btn.contains(e.target)) {
                panel.style.display = 'none';
                btn.classList.remove('nm-panel-open');
            }
        });

        // Prevent panel clicks from closing
        panel.addEventListener('click', (e) => e.stopPropagation());

        // Slider value labels
        const depthSlider = document.getElementById('nm-max-depth');
        const depthVal = document.getElementById('nm-depth-val');
        const devicesSlider = document.getElementById('nm-max-devices');
        const devicesVal = document.getElementById('nm-devices-val');
        if (depthSlider && depthVal) {
            depthSlider.addEventListener('input', () => { depthVal.textContent = depthSlider.value; });
        }
        if (devicesSlider && devicesVal) {
            devicesSlider.addEventListener('input', () => { devicesVal.textContent = devicesSlider.value; });
        }

        // Start discovery
        const startBtn = document.getElementById('nm-start-discovery');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startDiscovery());
        }

        // Stop discovery
        const stopBtn = document.getElementById('nm-stop-discovery');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopDiscovery());
        }

        // Generate topology
        const genBtn = document.getElementById('nm-generate-topology');
        if (genBtn) {
            genBtn.addEventListener('click', () => this.generateTopology());
        }

        // Map All (MCP) — queries backend MCP for all devices, no SSH
        const mapAllBtn = document.getElementById('nm-map-all');
        if (mapAllBtn) {
            mapAllBtn.addEventListener('click', () => this.mapAllFromMCP());
        }

        // Save topology
        const saveBtn = document.getElementById('nm-save-topology');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveTopology());
        }

        // Dismiss
        const dismissBtn = document.getElementById('nm-dismiss');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => this._resetPanel());
        }

        // Keyboard shortcut: N
        document.addEventListener('keydown', (e) => {
            if (e.key.toLowerCase() === 'n' && !e.ctrlKey && !e.metaKey && !e.altKey &&
                !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName) &&
                !document.activeElement?.isContentEditable) {
                btn.click();
            }
        });

        console.log('[OK] NetworkMapperManager panel setup complete');
    }

    _closeOtherPanels() {
        // Close DNAAS panel
        const dnaasPanel = document.getElementById('dnaas-panel');
        const dnaasBtn = document.getElementById('btn-dnaas');
        if (dnaasPanel && dnaasPanel.style.display === 'block') {
            dnaasPanel.style.display = 'none';
            if (dnaasBtn) dnaasBtn.classList.remove('dnaas-panel-open');
        }
        // Close Topologies dropdown
        const topoDD = document.getElementById('topologies-dropdown-menu');
        const topoBtn = document.getElementById('btn-topologies');
        if (topoDD && topoDD.style.display === 'block') {
            topoDD.style.display = 'none';
            if (topoBtn) topoBtn.classList.remove('topologies-open');
        }
    }

    _positionPanel(btn, panel) {
        const rect = btn.getBoundingClientRect();
        panel.style.top = (rect.bottom + 8) + 'px';
        panel.style.left = Math.max(10, rect.left - 200) + 'px';
    }

    // ========== DEVICE SUGGESTIONS ==========

    async populateSuggestions() {
        const section = document.getElementById('nm-suggestions-section');
        const list = document.getElementById('nm-suggestions-list');
        const countEl = document.getElementById('nm-suggestions-count');
        if (!section || !list) return;

        list.innerHTML = '';
        const seen = new Set();
        const devices = [];

        // Strip timestamps like "(12-Jan-2026-16:34:08)" and trailing commas
        const cleanName = (s) => (s || '').replace(/\([\d]+-[A-Za-z]+-\d{4}-[\d:]+\)\s*$/, '').replace(/,\s*$/, '').trim();
        const norm = (s) => cleanName(s).toLowerCase().replace(/[^a-z0-9]/g, '');

        const isSeen = (...keys) => keys.some(k => { const n = norm(k); return n && seen.has(n); });
        const markSeen = (...keys) => keys.forEach(k => { const n = norm(k); if (n) seen.add(n); });

        const addDevice = (name, addr, source, extraKeys) => {
            name = cleanName(name);
            const allKeys = [name, addr, ...(extraKeys || [])];
            const dupe = isSeen(...allKeys);
            markSeen(...allKeys);
            if (dupe) return;
            devices.push({ name, addr, source });
        };

        // Only show devices on the canvas that have SSH credentials, IP, or serial
        for (const obj of this.editor.objects) {
            if (obj.type !== 'device') continue;
            const label = obj.name || obj.label || obj.id;
            const host = obj.sshConfig?.host || '';
            const hostBackup = obj.sshConfig?.hostBackup || '';
            const serial = obj.deviceSerial || '';
            const addr = hostBackup || host || serial || '';
            if (addr) addDevice(label, addr, 'canvas', [host, hostBackup, serial]);
        }

        if (devices.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        if (countEl) countEl.textContent = devices.length;

        for (const dev of devices) {
            const btn = document.createElement('button');
            btn.style.cssText = `
                display: inline-flex; align-items: center; gap: 5px;
                padding: 4px 10px; border-radius: 8px;
                background: rgba(6, 182, 212, 0.1);
                border: 1px solid rgba(6, 182, 212, 0.2);
                color: rgba(255, 255, 255, 0.8); font-size: 11px;
                cursor: pointer; transition: all 0.15s;
                white-space: nowrap;
            `;
            btn.innerHTML = `<span style="font-weight:600;color:rgba(6,182,212,0.9);">${this._escapeHtml(dev.name)}</span>`;
            if (dev.addr && dev.addr !== dev.name) {
                btn.innerHTML += `<span style="font-size:9px;opacity:0.5;">${this._escapeHtml(dev.addr)}</span>`;
            }

            btn.addEventListener('mouseenter', () => {
                btn.style.background = 'rgba(6, 182, 212, 0.25)';
                btn.style.borderColor = 'rgba(6, 182, 212, 0.5)';
            });
            btn.addEventListener('mouseleave', () => {
                btn.style.background = 'rgba(6, 182, 212, 0.1)';
                btn.style.borderColor = 'rgba(6, 182, 212, 0.2)';
            });

            btn.addEventListener('click', () => {
                const input = document.getElementById('nm-seed-input');
                if (!input) return;
                const current = input.value.trim();
                const seedVal = dev.addr || dev.name;
                if (current) {
                    // Append if not already present
                    const existing = current.split(',').map(s => s.trim().toLowerCase());
                    if (!existing.includes(seedVal.toLowerCase())) {
                        input.value = current + ', ' + seedVal;
                    }
                } else {
                    input.value = seedVal;
                }
                // Visual feedback
                btn.style.background = 'rgba(39, 174, 96, 0.3)';
                btn.style.borderColor = 'rgba(39, 174, 96, 0.5)';
                setTimeout(() => {
                    btn.style.background = 'rgba(6, 182, 212, 0.1)';
                    btn.style.borderColor = 'rgba(6, 182, 212, 0.2)';
                }, 500);
            });

            list.appendChild(btn);
        }
    }

    _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ========== DISCOVERY CONTROL ==========

    async startDiscovery() {
        const seedInput = document.getElementById('nm-seed-input');
        const useInventory = document.getElementById('nm-use-inventory')?.checked || false;
        const useMcp = document.getElementById('nm-use-mcp')?.checked ?? true;
        const username = document.getElementById('nm-username')?.value || 'dnroot';
        const password = document.getElementById('nm-password')?.value || 'dnroot';
        const maxDepth = parseInt(document.getElementById('nm-max-depth')?.value || '10');
        const maxDevices = parseInt(document.getElementById('nm-max-devices')?.value || '50');

        const seeds = (seedInput?.value || '').split(',').map(s => s.trim()).filter(Boolean);

        if (seeds.length === 0 && !useInventory) {
            this.editor.showToast('Enter at least one seed device IP or hostname', 'warning');
            return;
        }

        // Collect canvas devices with SSH config for DNAAS-aware resolution
        const knownDevices = this.editor.objects
            .filter(o => o.type === 'device' && (o.sshConfig?.host || o.deviceSerial))
            .map(o => ({
                name: o.name || o.label || '',
                host: o.sshConfig?.host || '',
                hostBackup: o.sshConfig?.hostBackup || '',
                user: o.sshConfig?.user || '',
                password: o.sshConfig?.password || '',
                serial: o.deviceSerial || ''
            }));
        this._discoveryCredentials = { username, password };

        // Show progress section
        this._showProgress();
        this._setStatus('Discovering...', 'running');

        const btn = document.getElementById('btn-network-mapper');
        if (btn) btn.classList.add('nm-running');

        try {
            const resp = await fetch('/api/network-mapper/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    seeds,
                    use_inventory: useInventory,
                    use_network_mapper_mcp: useMcp,
                    max_depth: maxDepth,
                    max_devices: maxDevices,
                    credentials: { username, password },
                    known_devices: knownDevices
                })
            });
            const data = await resp.json();
            if (data.error) {
                this._setStatus('Error', 'error');
                this.editor.showToast('Discovery failed: ' + data.error, 'error');
                if (btn) btn.classList.remove('nm-running');
                return;
            }

            this._jobId = data.job_id;
            this._startPolling();
        } catch (err) {
            this._setStatus('Error', 'error');
            this.editor.showToast('Discovery request failed: ' + err.message, 'error');
            if (btn) btn.classList.remove('nm-running');
        }
    }

    async stopDiscovery() {
        if (!this._jobId) return;
        try {
            await fetch('/api/network-mapper/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_id: this._jobId })
            });
        } catch (e) {
            console.warn('[NetworkMapper] Stop failed:', e);
        }
    }

    async mapAllFromMCP() {
        this._showProgress();
        this._setStatus('Querying Network Mapper...', 'running');
        this._autoGenerate = true;
        const btn = document.getElementById('btn-network-mapper');
        if (btn) btn.classList.add('nm-running');

        try {
            const resp = await fetch('/api/network-mapper/mcp-map', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            });
            const data = await resp.json();
            if (data.error) {
                this._setStatus('Error', 'error');
                this.editor.showToast('MCP map failed: ' + data.error, 'error');
                if (btn) btn.classList.remove('nm-running');
                return;
            }
            this._jobId = data.job_id;
            this._startPolling();
        } catch (err) {
            this._setStatus('Error', 'error');
            this.editor.showToast('MCP map request failed: ' + err.message, 'error');
            if (btn) btn.classList.remove('nm-running');
        }
    }

    _startPolling() {
        this._pollFailureCount = 0;
        if (this._pollInterval) clearInterval(this._pollInterval);
        this._pollInterval = setInterval(() => this._pollStatus(), 2000);
        this._pollStatus();
    }

    async _pollStatus() {
        if (!this._jobId) return;
        try {
            const resp = await fetch(`/api/network-mapper/status?job_id=${this._jobId}`);
            const data = await resp.json();
            if (data.error) {
                this._pollFailureCount++;
                if (this._pollFailureCount >= 3) {
                    this.editor.showToast('Network Mapper API not responding -- check if discovery_api.py is running', 'warning');
                    this._pollFailureCount = 0;
                }
                return;
            }
            this._pollFailureCount = 0;

            // Update progress UI
            const progress = data.progress || {};
            const discovered = progress.discovered || 0;
            const max = progress.max || 50;
            const queued = progress.queued || 0;
            const failed = progress.failed || 0;

            const progressText = document.getElementById('nm-progress-text');
            const progressBar = document.getElementById('nm-progress-bar');
            const countDiscovered = document.getElementById('nm-count-discovered');
            const countQueued = document.getElementById('nm-count-queued');
            const countFailed = document.getElementById('nm-count-failed');
            const logOutput = document.getElementById('nm-log-output');

            if (progressText) progressText.textContent = `Discovered ${discovered} device${discovered !== 1 ? 's' : ''}...`;
            if (progressBar) progressBar.style.width = Math.min(100, (discovered / max) * 100) + '%';
            if (countDiscovered) countDiscovered.textContent = discovered;
            if (countQueued) countQueued.textContent = queued;
            if (countFailed) countFailed.textContent = failed;

            // Update log
            if (logOutput && data.log) {
                logOutput.textContent = data.log.join('\n');
                logOutput.scrollTop = logOutput.scrollHeight;
            }

            // Check completion
            if (data.status === 'completed' || data.status === 'cancelled' || data.status === 'error') {
                clearInterval(this._pollInterval);
                this._pollInterval = null;
                this._lastDiscoveryData = data;

                const btn = document.getElementById('btn-network-mapper');
                if (btn) {
                    btn.classList.remove('nm-running');
                    if (data.status === 'completed') btn.classList.add('nm-complete');
                }

                const spinner = document.getElementById('nm-spinner');
                if (spinner) spinner.style.display = 'none';

                if (progressText) {
                    progressText.textContent = data.status === 'completed'
                        ? `Done: ${discovered} devices, ${(data.links || []).length} links`
                        : data.status === 'cancelled' ? 'Cancelled' : 'Error';
                }

                this._setStatus(data.status === 'completed' ? 'Complete' : data.status, data.status);
                this._showResultActions();

                if (data.status === 'completed' && discovered > 0) {
                    this.editor.showToast(`Discovery complete: ${discovered} devices, ${(data.links || []).length} links`, 'success');
                    // Auto-generate topology for MCP-map (user doesn't need to click again)
                    if (this._autoGenerate) {
                        this._autoGenerate = false;
                        setTimeout(() => this.generateTopology(), 300);
                    }
                }
            }
        } catch (err) {
            console.warn('[NetworkMapper] Poll failed:', err);
            this._pollFailureCount++;
            if (this._pollFailureCount >= 3) {
                this.editor.showToast('Network Mapper API not responding -- check if discovery_api.py is running', 'warning');
                this._pollFailureCount = 0;
            }
        }
    }

    // ========== TOPOLOGY GENERATION (debug-dnos quality) ==========

    generateTopology() {
        const data = this._lastDiscoveryData;
        if (!data || !data.devices) {
            this.editor.showToast('No discovery data available', 'warning');
            return;
        }

        const devices = data.devices;
        const links = data.links || [];
        const deviceNames = Object.keys(devices);

        if (deviceNames.length === 0) {
            this.editor.showToast('No devices discovered', 'warning');
            return;
        }

        // Build name lookup (case-insensitive) so links find their endpoints
        const nameLookup = {};
        for (const name of deviceNames) {
            nameLookup[name.toLowerCase()] = name;
            const hostname = (devices[name].hostname || '').toLowerCase();
            if (hostname && !nameLookup[hostname]) nameLookup[hostname] = name;
        }
        const resolveDeviceName = (n) => nameLookup[n.toLowerCase()] || null;

        // Classify and compute layout
        const classified = {};
        for (const name of deviceNames) {
            classified[name] = this._classifyDevice(devices[name]);
        }
        const positions = this._hybridLayout(deviceNames, links, devices, classified);

        // Build topology data object compatible with loadTopologyFromData
        const objects = [];
        const deviceMap = {};
        const creds = this._discoveryCredentials || { username: 'dnroot', password: 'dnroot' };
        let devCounter = 0, linkCounter = 0, textCounter = 0;

        // --- LAYER 1: Devices (drawn first = bottom z-order) ---
        for (const name of deviceNames) {
            const dev = devices[name];
            const cls = classified[name];
            const pos = positions[name] || { x: 400, y: 400 };
            const isFailed = dev._failed || dev.source === 'lldp_stub';

            const deviceObj = {
                type: 'device',
                id: `device_${devCounter++}`,
                deviceType: 'router',
                x: pos.x,
                y: pos.y,
                radius: isFailed ? 25 : cls.radius,
                rotation: 0,
                color: isFailed ? '#7f8c8d' : cls.color,
                label: dev.hostname || name,
                locked: false,
                visualStyle: isFailed ? 'simple' : cls.visualStyle
            };

            const connectHost = dev.mgmt_ip || dev._connect_host || '';
            if (connectHost || dev.serial) {
                deviceObj.sshConfig = {
                    host: connectHost,
                    hostBackup: dev.serial || dev.hostname || '',
                    user: creds.username || 'dnroot',
                    password: creds.password || 'dnroot'
                };
            }
            if (dev.serial) deviceObj.deviceSerial = dev.serial;

            objects.push(deviceObj);
            deviceMap[name] = deviceObj;
        }

        // --- LAYER 2: Links ---
        const linkPairSeen = new Set();
        const createdLinks = [];
        for (const link of links) {
            const fromKey = resolveDeviceName(link.from_device);
            const toKey = resolveDeviceName(link.to_device);
            const fromDev = fromKey ? deviceMap[fromKey] : null;
            const toDev = toKey ? deviceMap[toKey] : null;
            if (!fromDev || !toDev || fromDev.id === toDev.id) continue;

            const pairKey = [fromDev.id, toDev.id].sort().join(':');
            if (linkPairSeen.has(pairKey)) continue;
            linkPairSeen.add(pairKey);

            const ls = this._getLinkStyle(link, devices);
            const linkObj = {
                type: 'link',
                id: `link_${linkCounter++}`,
                originType: 'QL',
                device1: fromDev.id,
                device2: toDev.id,
                start: { x: fromDev.x, y: fromDev.y },
                end: { x: toDev.x, y: toDev.y },
                color: ls.color,
                style: ls.style,
                width: ls.width,
                interface1: link.from_interface || '',
                interface2: link.to_interface || ''
            };
            objects.push(linkObj);
            createdLinks.push({ linkObj, link, fromKey, toKey });
        }

        // --- LAYER 3: Text labels ---

        // Protocol + interface labels on each link
        for (const { linkObj, link, fromKey, toKey } of createdLinks) {
            const fromCls = classified[fromKey];
            const toCls = classified[toKey];
            const protocol = this._inferProtocol(link, fromCls, toCls);
            const ifFrom = this._shortenInterface(link.from_interface || '');
            const ifTo = this._shortenInterface(link.to_interface || '');

            let labelText = protocol;
            if (ifFrom || ifTo) {
                labelText = `${protocol}\n${ifFrom} ↔ ${ifTo}`;
            }

            const midX = (linkObj.start.x + linkObj.end.x) / 2;
            const midY = (linkObj.start.y + linkObj.end.y) / 2;

            objects.push({
                type: 'text',
                id: `text_${textCounter++}`,
                x: midX,
                y: midY,
                text: labelText,
                fontSize: 8,
                color: linkObj.color,
                linkId: linkObj.id,
                linkAttachT: 0.5,
                position: 'middle',
                _onLinkLine: true,
                showBackground: false
            });
        }

        // IP address labels below each device
        for (const name of deviceNames) {
            const dev = devices[name];
            const devObj = deviceMap[name];
            const ip = dev.mgmt_ip || '';
            if (!ip || !/^\d/.test(ip)) continue;

            objects.push({
                type: 'text',
                id: `text_${textCounter++}`,
                x: devObj.x,
                y: devObj.y + devObj.radius + 26,
                text: ip,
                fontSize: 10,
                color: '#85929e',
                showBackground: false
            });
        }

        // System info above devices (compact, only when meaningful)
        for (const name of deviceNames) {
            const dev = devices[name];
            const devObj = deviceMap[name];
            const parts = [];
            if (dev.system_type) parts.push(dev.system_type);
            if (dev.dnos_version) {
                const ver = dev.dnos_version.replace(/^.*?(\d+\.\d+).*$/, '$1');
                if (ver) parts.push('v' + ver);
            }
            if (parts.length === 0) continue;

            objects.push({
                type: 'text',
                id: `text_${textCounter++}`,
                x: devObj.x,
                y: devObj.y - devObj.radius - 24,
                text: parts.join(' | '),
                fontSize: 8,
                color: '#aeb6bf',
                showBackground: false
            });
        }

        // Load via editor's standard mechanism (handles state, groups, BD, drawing, centering)
        this.editor.loadTopologyFromData({
            version: '1.0',
            objects: objects,
            metadata: {
                deviceIdCounter: devCounter,
                linkIdCounter: linkCounter,
                textIdCounter: textCounter,
                shapeIdCounter: 0,
                description: `Network Mapper: ${deviceNames.length} devices`
            }
        });

        // Enable link text visibility so protocol/interface labels are shown
        this.editor.showLinkAttachments = true;
        localStorage.setItem('topology_showLinkAttachments', 'true');
        const linkAttachBtn = document.getElementById('btn-link-attachments');
        if (linkAttachBtn) {
            linkAttachBtn.classList.add('active');
            const statusText = linkAttachBtn.querySelector('.status-text');
            if (statusText) statusText.textContent = 'Link Text: ON';
        }

        this.editor.draw();

        this.editor.showToast(
            `Topology generated: ${deviceNames.length} devices, ${linkCounter} links`,
            'success'
        );
    }

    // ========== DEVICE CLASSIFICATION ==========

    _classifyDevice(dev) {
        const sysType = (dev.system_type || '').toLowerCase();
        const hostname = (dev.hostname || '').toLowerCase();

        // Drivenets platform detection from system_type (SA=standalone, CL=cluster, NCR=combined)
        const isNCR = sysType.includes('ncr') || sysType.startsWith('sa-') || sysType.startsWith('cl-');
        const isSA = sysType.startsWith('sa-');
        const isCL = sysType.startsWith('cl-');

        if (sysType.includes('ncm') || hostname.includes('ncm') || hostname.includes('superspine')) {
            return { role: 'NCM', tier: 0, visualStyle: 'server', color: '#c0392b', radius: 50 };
        }
        if (hostname.includes('spine') && !hostname.includes('superspine')) {
            return { role: 'spine', tier: 0, visualStyle: 'server', color: '#9b59b6', radius: 50 };
        }
        if (sysType.includes('ncc') || hostname.includes('ncc') || hostname.includes('rr')) {
            return { role: 'NCC', tier: 0, visualStyle: 'classic', color: '#9b59b6', radius: 40 };
        }
        if (sysType.includes('ncf') || hostname.includes('ncf') || hostname.includes('leaf')) {
            return { role: 'NCF', tier: 1, visualStyle: 'classic', color: '#3498db', radius: 40 };
        }
        if (hostname.includes('pe') || hostname.includes('router') || hostname.includes('dut')) {
            return { role: 'PE', tier: 1, visualStyle: 'classic', color: '#3498db', radius: 40 };
        }
        if (hostname.includes('ce') || hostname.includes('customer')) {
            return { role: 'CE', tier: 2, visualStyle: 'simple', color: '#2ecc71', radius: 30 };
        }
        if (hostname.includes('exabgp') || hostname.includes('ixia') || hostname.includes('tester')) {
            return { role: 'external', tier: 2, visualStyle: 'server', color: '#e67e22', radius: 30 };
        }
        if (hostname.includes('arista') || hostname.includes('juniper') || hostname.includes('cisco')) {
            return { role: 'external', tier: 2, visualStyle: 'simple', color: '#e67e22', radius: 30 };
        }
        if (isCL) {
            return { role: 'NCR', tier: 1, visualStyle: 'classic', color: '#2980b9', radius: 45 };
        }
        if (isSA) {
            return { role: 'NCR', tier: 1, visualStyle: 'classic', color: '#3498db', radius: 40 };
        }
        return { role: 'router', tier: 1, visualStyle: 'classic', color: '#3498db', radius: 40 };
    }

    // ========== LINK STYLING ==========

    _getLinkStyle(link, devices) {
        const fromIf = (link.from_interface || '').toLowerCase();
        const toIf = (link.to_interface || '').toLowerCase();
        const isBundleEther = fromIf.includes('bundle-ether') || toIf.includes('bundle-ether');
        const isBundle = fromIf.includes('bundle') || toIf.includes('bundle');
        const isGe400 = fromIf.includes('ge400') || toIf.includes('ge400');
        const isHu400 = fromIf.includes('hu400') || toIf.includes('hu400');
        const isCe400 = fromIf.includes('ce400') || toIf.includes('ce400');
        const isMgmt = fromIf.includes('mgmt') || toIf.includes('mgmt');

        if (isBundleEther || isBundle) {
            return { color: '#2ecc71', style: 'solid', width: 3 };
        }
        if (isHu400 || isCe400) {
            return { color: '#e67e22', style: 'solid', width: 2 };
        }
        if (isGe400) {
            return { color: '#85c1e9', style: 'solid', width: 2 };
        }
        if (isMgmt) {
            return { color: '#95a5a6', style: 'dashed', width: 1 };
        }
        return { color: '#85c1e9', style: 'solid', width: 2 };
    }

    _shortenInterface(ifName) {
        return ifName
            .replace('ge400-', 'ge4/')
            .replace('ge100-', 'ge1/')
            .replace('hu400-', 'hu4/')
            .replace('ce400-', 'ce4/')
            .replace('bundle-ether', 'BE')
            .replace('hundredGigE-', '100G/')
            .replace('tenGigE-', '10G/')
            .replace('fortyGigE-', '40G/');
    }

    /**
     * Infer routing protocol from interface names, device roles, and link context.
     * Returns a short protocol label for display on the link.
     */
    _inferProtocol(link, fromClassified, toClassified) {
        const fromIf = (link.from_interface || '').toLowerCase();
        const toIf = (link.to_interface || '').toLowerCase();
        const fromRole = fromClassified ? fromClassified.role : '';
        const toRole = toClassified ? toClassified.role : '';
        const isMgmt = fromIf.includes('mgmt') || toIf.includes('mgmt');
        const isBE = fromIf.includes('bundle-ether') || toIf.includes('bundle-ether');
        const isGe400 = fromIf.includes('ge400') || toIf.includes('ge400');
        const isGe100 = fromIf.includes('ge100') || toIf.includes('ge100');
        const isGe10 = fromIf.includes('ge10-') || toIf.includes('ge10-');

        if (isMgmt) return 'MGMT';

        const dnosRoles = new Set(['NCM', 'NCF', 'NCR', 'spine', 'NCC', 'PE']);
        const fabricRoles = new Set(['NCM', 'NCF', 'NCR', 'spine', 'NCC']);
        const bothDNOS = dnosRoles.has(fromRole) && dnosRoles.has(toRole);
        const bothFabric = fabricRoles.has(fromRole) && fabricRoles.has(toRole);

        // NCR-to-NCR links on ge400 are typically ISIS fabric interconnects
        if (bothDNOS && isGe400) return 'ISIS';
        if (bothDNOS && isGe100) return 'ISIS';
        if (bothDNOS && isGe10) return 'ISIS';
        if (bothDNOS && isBE) return 'ISIS / LAG';

        const rrInvolved = fromRole === 'NCC' || toRole === 'NCC';
        if (rrInvolved) return 'iBGP / ISIS';

        const ceInvolved = fromRole === 'CE' || toRole === 'CE';
        const extInvolved = fromRole === 'external' || toRole === 'external';
        if (ceInvolved) return 'eBGP';
        if (extInvolved && bothDNOS) return 'ISIS';
        if (extInvolved) return 'L1';

        if (isBE) return 'LAG';
        if (isGe400) return '400G';
        if (isGe100) return '100G';
        if (isGe10) return '10G';

        return 'LLDP';
    }

    // ========== HYBRID LAYOUT ==========

    _hybridLayout(deviceNames, links, devices, classified) {
        const n = deviceNames.length;
        if (n === 0) return {};
        if (n === 1) return { [deviceNames[0]]: { x: 600, y: 400 } };

        // Group devices by tier
        const tiers = {};
        for (const name of deviceNames) {
            const tier = classified[name].tier;
            if (!tiers[tier]) tiers[tier] = [];
            tiers[tier].push(name);
        }

        const tierKeys = Object.keys(tiers).map(Number).sort();
        if (tierKeys.length <= 1) return this._forceDirectedLayout(deviceNames, links);

        // Build adjacency for neighbor-aware positioning
        const nameToIdx = {};
        deviceNames.forEach((name, i) => { nameToIdx[name] = i; });
        const adj = {};
        for (const name of deviceNames) adj[name] = new Set();
        const pairSeen = new Set();
        for (const link of links) {
            const a = link.from_device, b = link.to_device;
            if (!adj[a] || !adj[b]) continue;
            const k = [a, b].sort().join(':');
            if (pairSeen.has(k)) continue;
            pairSeen.add(k);
            adj[a].add(b);
            adj[b].add(a);
        }

        // Tier Y positioning with generous vertical spacing
        const tierSpacingY = 300;
        const startY = 250;
        const tierY = {};
        tierKeys.forEach((t, i) => { tierY[t] = startY + i * tierSpacingY; });

        // Per-tier X positioning: sort by connectivity barycenter, then space evenly
        const positions = {};
        const minGapX = 220;

        // Process tiers top-down so upper tiers inform lower positions
        for (const t of tierKeys) {
            const tierDevs = tiers[t];
            const tn = tierDevs.length;

            // Compute desired X (barycenter of already-placed neighbors)
            const desiredX = {};
            for (const name of tierDevs) {
                const placed = [...adj[name]].filter(nb => positions[nb]);
                if (placed.length > 0) {
                    desiredX[name] = placed.reduce((s, nb) => s + positions[nb].x, 0) / placed.length;
                } else {
                    desiredX[name] = null;
                }
            }

            // Sort: devices with barycenter first (by desired X), then unconnected
            const withBary = tierDevs.filter(d => desiredX[d] !== null).sort((a, b) => desiredX[a] - desiredX[b]);
            const noBary = tierDevs.filter(d => desiredX[d] === null);
            const sorted = [...withBary, ...noBary];

            // Initial placement: spread evenly
            const totalWidth = (tn - 1) * minGapX;
            const centerX = 600;
            const xStart = centerX - totalWidth / 2;

            const xPos = {};
            sorted.forEach((name, i) => {
                if (desiredX[name] !== null) {
                    xPos[name] = desiredX[name];
                } else {
                    xPos[name] = xStart + i * minGapX;
                }
            });

            // Resolve overlaps: sort by X, enforce minimum gap
            for (let pass = 0; pass < 10; pass++) {
                const order = [...sorted].sort((a, b) => xPos[a] - xPos[b]);
                for (let i = 1; i < order.length; i++) {
                    const gap = xPos[order[i]] - xPos[order[i - 1]];
                    if (gap < minGapX) {
                        const push = (minGapX - gap) / 2 + 5;
                        xPos[order[i]] += push;
                        xPos[order[i - 1]] -= push;
                    }
                }
            }

            const y = tierY[t];
            for (const name of sorted) {
                positions[name] = { x: Math.round(xPos[name]), y };
            }
        }

        // Center entire topology around viewport center
        let minX = Infinity, maxX = -Infinity;
        for (const p of Object.values(positions)) {
            minX = Math.min(minX, p.x);
            maxX = Math.max(maxX, p.x);
        }
        const mid = (minX + maxX) / 2;
        const shift = 600 - mid;
        for (const p of Object.values(positions)) {
            p.x = Math.round(p.x + shift);
        }

        return positions;
    }

    _forceDirectedLayout(deviceNames, links) {
        const n = deviceNames.length;
        if (n === 0) return {};
        if (n === 1) return { [deviceNames[0]]: { x: 600, y: 400 } };

        // Build adjacency
        const nameToIdx = {};
        deviceNames.forEach((name, i) => { nameToIdx[name] = i; });
        const adj = Array.from({ length: n }, () => new Set());
        const pairSeen = new Set();
        for (const link of links) {
            const i = nameToIdx[link.from_device];
            const j = nameToIdx[link.to_device];
            if (i === undefined || j === undefined || i === j) continue;
            const k = Math.min(i, j) + ':' + Math.max(i, j);
            if (pairSeen.has(k)) continue;
            pairSeen.add(k);
            adj[i].add(j);
            adj[j].add(i);
        }

        // Initial placement: grid layout (much better than circle for convergence)
        const cols = Math.ceil(Math.sqrt(n));
        const gridSpacing = 250;
        const cx = 600, cy = 400;
        const gridW = (cols - 1) * gridSpacing;
        const pos = deviceNames.map((_, i) => ({
            x: cx - gridW / 2 + (i % cols) * gridSpacing,
            y: cy - gridW / 2 + Math.floor(i / cols) * gridSpacing
        }));

        const idealDist = Math.max(250, 2400 / Math.sqrt(n));
        const iterations = Math.min(300, 80 + n * 4);

        for (let iter = 0; iter < iterations; iter++) {
            const temp = Math.max(0.01, 1 - iter / iterations);
            const forces = pos.map(() => ({ fx: 0, fy: 0 }));

            // Repulsion between all pairs
            for (let i = 0; i < n; i++) {
                for (let j = i + 1; j < n; j++) {
                    const dx = pos[j].x - pos[i].x;
                    const dy = pos[j].y - pos[i].y;
                    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 10);
                    const repForce = (idealDist * idealDist) / dist;
                    const ux = dx / dist, uy = dy / dist;
                    forces[i].fx -= ux * repForce;
                    forces[i].fy -= uy * repForce;
                    forces[j].fx += ux * repForce;
                    forces[j].fy += uy * repForce;
                }
            }

            // Attraction along edges
            for (let i = 0; i < n; i++) {
                for (const j of adj[i]) {
                    if (j <= i) continue;
                    const dx = pos[j].x - pos[i].x;
                    const dy = pos[j].y - pos[i].y;
                    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 10);
                    const attForce = dist / idealDist;
                    const ux = dx / dist, uy = dy / dist;
                    forces[i].fx += ux * attForce * 0.5;
                    forces[i].fy += uy * attForce * 0.5;
                    forces[j].fx -= ux * attForce * 0.5;
                    forces[j].fy -= uy * attForce * 0.5;
                }
            }

            // Gentle gravity toward center
            for (let i = 0; i < n; i++) {
                forces[i].fx += (cx - pos[i].x) * 0.005;
                forces[i].fy += (cy - pos[i].y) * 0.005;
            }

            const maxDisp = idealDist * temp * 0.3;
            for (let i = 0; i < n; i++) {
                const fMag = Math.sqrt(forces[i].fx ** 2 + forces[i].fy ** 2) || 1;
                const disp = Math.min(fMag, maxDisp);
                pos[i].x += (forces[i].fx / fMag) * disp;
                pos[i].y += (forces[i].fy / fMag) * disp;
            }
        }

        // Normalize: ensure minimum 200px from origin
        let minX = Infinity, minY = Infinity;
        for (const p of pos) {
            minX = Math.min(minX, p.x);
            minY = Math.min(minY, p.y);
        }
        const offX = 250 - minX;
        const offY = 250 - minY;

        const result = {};
        deviceNames.forEach((name, i) => {
            result[name] = {
                x: Math.round(pos[i].x + offX),
                y: Math.round(pos[i].y + offY)
            };
        });
        return result;
    }

    // ========== DOMAIN / SAVE ==========

    async _ensureNetworkMapperSection() {
        if (this._sectionId) return this._sectionId;
        try {
            const resp = await fetch('/api/sections');
            const data = await resp.json();
            const sections = data.sections || [];
            const existing = sections.find(s => s.name === 'Network Mapper');
            if (existing) {
                this._sectionId = existing.id;
                return existing.id;
            }
            // Create the section
            const createResp = await fetch('/api/sections', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'Network Mapper', color: '#06b6d4', icon: 'wifi' })
            });
            const created = await createResp.json();
            this._sectionId = created.id;
            if (this.editor.loadCustomSections) this.editor.loadCustomSections();
            return created.id;
        } catch (err) {
            console.error('[NetworkMapper] Failed to ensure section:', err);
            throw err;
        }
    }

    async saveTopology() {
        try {
            const sectionId = await this._ensureNetworkMapperSection();
            const data = this._lastDiscoveryData || {};
            const deviceCount = Object.keys(data.devices || {}).length;
            const seedName = Object.values(data.devices || {})[0]?.hostname || 'unknown';
            const timestamp = new Date().toISOString().slice(0, 16).replace('T', ' ');
            const name = `Network Map - ${seedName} - ${timestamp}`;

            const topoData = this.editor.generateTopologyData
                ? this.editor.generateTopologyData()
                : (window.FileOps?.generateTopologyData
                    ? window.FileOps.generateTopologyData(this.editor)
                    : null);

            if (!topoData) {
                this.editor.showToast('Cannot generate topology data', 'error');
                return;
            }

            // Add network mapper metadata
            topoData.metadata = topoData.metadata || {};
            topoData.metadata.networkMapper = {
                discoveredAt: new Date().toISOString(),
                seedDevices: (data.devices ? Object.keys(data.devices) : []).slice(0, 5),
                deviceCount: deviceCount,
                linkCount: (data.links || []).length,
                jobId: this._jobId
            };

            const resp = await fetch(`/api/sections/${sectionId}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, topology: topoData })
            });
            const result = await resp.json();
            if (result.error) throw new Error(result.error);

            if (window.FileOps?.updateTopologyIndicator) {
                window.FileOps.updateTopologyIndicator(this.editor, name, 'Network Mapper', '#06b6d4', sectionId);
            }

            this.editor.showToast(`Saved to Network Mapper: ${name}`, 'success');
        } catch (err) {
            this.editor.showToast('Save failed: ' + err.message, 'error');
        }
    }

    // ========== UI HELPERS ==========

    _showProgress() {
        const progressSection = document.getElementById('nm-progress-section');
        const resultActions = document.getElementById('nm-result-actions');
        const spinner = document.getElementById('nm-spinner');
        const logOutput = document.getElementById('nm-log-output');
        const progressBar = document.getElementById('nm-progress-bar');

        if (progressSection) progressSection.style.display = 'block';
        if (resultActions) resultActions.style.display = 'none';
        if (spinner) spinner.style.display = 'block';
        if (logOutput) logOutput.textContent = '';
        if (progressBar) progressBar.style.width = '0%';
    }

    _showResultActions() {
        const resultActions = document.getElementById('nm-result-actions');
        if (resultActions) resultActions.style.display = 'flex';
    }

    _setStatus(text, state) {
        const status = document.getElementById('nm-panel-status');
        if (!status) return;
        status.textContent = text;
        const colors = {
            running: { bg: 'rgba(6, 182, 212, 0.2)', color: 'rgba(6, 182, 212, 0.9)' },
            completed: { bg: 'rgba(39, 174, 96, 0.2)', color: 'rgba(39, 174, 96, 0.9)' },
            complete: { bg: 'rgba(39, 174, 96, 0.2)', color: 'rgba(39, 174, 96, 0.9)' },
            error: { bg: 'rgba(231, 76, 60, 0.2)', color: 'rgba(231, 76, 60, 0.9)' },
            cancelled: { bg: 'rgba(241, 196, 15, 0.2)', color: 'rgba(241, 196, 15, 0.9)' }
        };
        const c = colors[state] || { bg: 'rgba(39, 174, 96, 0.2)', color: 'rgba(255, 255, 255, 0.9)' };
        status.style.background = c.bg;
        status.style.color = c.color;
    }

    _resetPanel() {
        const progressSection = document.getElementById('nm-progress-section');
        const resultActions = document.getElementById('nm-result-actions');
        if (progressSection) progressSection.style.display = 'none';
        if (resultActions) resultActions.style.display = 'none';
        this._setStatus('Ready', 'ready');
        this._lastDiscoveryData = null;
        this._jobId = null;

        const btn = document.getElementById('btn-network-mapper');
        if (btn) {
            btn.classList.remove('nm-running', 'nm-complete');
        }
    }
}

window.NetworkMapperManager = NetworkMapperManager;
