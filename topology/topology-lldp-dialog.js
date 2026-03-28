/**
 * topology-lldp-dialog.js - LLDP Table Dialog Module
 * 
 * Contains the LLDP neighbor discovery table dialog
 */

'use strict';

window.LldpDialog = {
    showLldpTableDialog(editor, device, serial, options = {}) {
        const self = this;
        const forceRefresh = options.forceRefresh || false;
        const existingDialog = document.getElementById('lldp-table-dialog');
        if (existingDialog && existingDialog.dataset.serial === serial) {
            if (forceRefresh) {
                existingDialog.remove();
            } else {
                existingDialog.remove();
                return;
            }
        }
        if (existingDialog) existingDialog.remove();
        
        // Clear the "new results" badge -- user is viewing the data
        if (device) {
            device._lldpNewResults = false;
            if (editor.draw) editor.draw();
        }
        
        // Get device label for header
        const deviceLabel = device?.label || serial;
        
        // Create dialog
        const dialog = document.createElement('div');
        dialog.id = 'lldp-table-dialog';
        dialog.dataset.serial = serial;
        dialog.style.cssText = `
            position: fixed;
            z-index: 10002;
            min-width: 500px;
            max-width: 800px;
            max-height: 70vh;
            background: rgba(20, 25, 35, 0.75);
            backdrop-filter: blur(40px) saturate(180%);
            -webkit-backdrop-filter: blur(40px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 2px 8px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        `;
        
        // Header (draggable)
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 18px;
            background: rgba(0, 180, 216, 0.1);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            cursor: move;
            user-select: none;
        `;
        header.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00B4D8" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M7.76 7.76a6 6 0 0 1 8.48 0"/>
                    <path d="M7.76 16.24a6 6 0 0 0 8.48 0"/>
                </svg>
                <span style="color: rgba(255, 255, 255, 0.95); font-weight: 600; font-size: 14px;">
                    LLDP Neighbors - ${deviceLabel}
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <button id="lldp-table-refresh" title="Refresh via live SSH" style="
                    background: rgba(0, 180, 216, 0.15);
                    border: 1px solid rgba(0, 180, 216, 0.3);
                    border-radius: 6px;
                    width: 28px;
                    height: 28px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.15s;
                ">
                    <svg id="lldp-refresh-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00B4D8" stroke-width="2.5" style="transition: transform 0.3s;">
                        <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                    </svg>
                </button>
                <button id="lldp-table-close" style="
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 6px;
                    width: 28px;
                    height: 28px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.15s;
                ">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
        `;
        
        // Content area
        const content = document.createElement('div');
        content.style.cssText = `
            padding: 16px;
            overflow-y: auto;
            flex: 1;
        `;
        content.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; padding: 40px; color: rgba(255,255,255,0.6);">
                <div style="width: 20px; height: 20px; border: 2px solid rgba(0, 180, 216, 0.5); border-top-color: #00B4D8; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 12px;"></div>
                Loading LLDP neighbors...
            </div>
            <style>@keyframes spin { to { transform: rotate(360deg); } }</style>
        `;
        
        dialog.appendChild(header);
        dialog.appendChild(content);
        
        // Keyboard isolation: prevent key events from reaching the global
        // editor keyboard handler while this dialog is open.
        dialog.addEventListener('keydown', (e) => { e.stopPropagation(); });
        dialog.addEventListener('keyup', (e) => { e.stopPropagation(); });
        dialog.tabIndex = -1;
        
        document.body.appendChild(dialog);
        dialog.focus();
        
        // Position dialog in center
        dialog.style.left = '50%';
        dialog.style.top = '50%';
        dialog.style.transform = 'translate(-50%, -50%)';
        
        // Make draggable by header
        let isDragging = false, startX, startY, startLeft, startTop;
        header.addEventListener('mousedown', (e) => {
            if (e.target.closest('button')) return;
            isDragging = true;
            const rect = dialog.getBoundingClientRect();
            startX = e.clientX;
            startY = e.clientY;
            startLeft = rect.left;
            startTop = rect.top;
            dialog.style.transform = 'none';
            dialog.style.left = startLeft + 'px';
            dialog.style.top = startTop + 'px';
        });
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            dialog.style.left = (startLeft + dx) + 'px';
            dialog.style.top = (startTop + dy) + 'px';
        });
        document.addEventListener('mouseup', () => isDragging = false);
        
        // Close button
        const closeBtn = header.querySelector('#lldp-table-close');
        closeBtn.addEventListener('mouseenter', () => closeBtn.style.background = 'rgba(231, 76, 60, 0.3)');
        closeBtn.addEventListener('mouseleave', () => closeBtn.style.background = 'rgba(255, 255, 255, 0.1)');
        const onContextUpdated = (e) => {
            const { deviceId } = e.detail || {};
            if (!deviceId || !device) return;
            const match = (device.label && device.label === deviceId) || (String(serial) === String(deviceId));
            if (match && device._lldpData && document.body.contains(dialog)) {
                updateLldpContent(device._lldpData, true);
            }
        };
        window.addEventListener('device:context-updated', onContextUpdated);
        closeBtn.addEventListener('click', () => {
            window.removeEventListener('device:context-updated', onContextUpdated);
            dialog.remove();
        });
        
        // Refresh button - triggers live SSH query
        const refreshBtn = header.querySelector('#lldp-table-refresh');
        const refreshIcon = header.querySelector('#lldp-refresh-icon');
        refreshBtn.addEventListener('mouseenter', () => {
            refreshBtn.style.background = 'rgba(0, 180, 216, 0.3)';
            refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.5)';
        });
        refreshBtn.addEventListener('mouseleave', () => {
            refreshBtn.style.background = 'rgba(0, 180, 216, 0.15)';
            refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.3)';
        });
        
        // Unified content renderer for both initial load and refresh
        const updateLldpContent = (data, fromCache = false) => {
            if (device && !fromCache && (data.neighbors?.length || data.raw_output)) {
                device._lldpData = data;
                device._lldpCompletedAt = Date.now();
                if (editor.draw) editor.draw();
            }
            if (data.neighbors && data.neighbors.length > 0) {
                const snakeGroups = self._detectSnakePatterns(data.neighbors, deviceLabel, device);
                let tableHtml = self._buildLldpTableHtml(snakeGroups, data, device, deviceLabel);
                content.innerHTML = tableHtml;
                self._attachLldpTableEvents(content, device, snakeGroups, dialog);
            } else if (data.raw_output) {
                content.innerHTML = `
                    <div style="margin-bottom: 12px; color: rgba(255, 193, 7, 0.9); font-size: 11px;">
                        Raw LLDP output (could not parse neighbors):
                    </div>
                    <pre style="
                        background: rgba(0, 0, 0, 0.3);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 8px;
                        padding: 12px;
                        color: rgba(255,255,255,0.8);
                        font-size: 11px;
                        font-family: 'Monaco', 'Menlo', monospace;
                        white-space: pre-wrap;
                        word-break: break-all;
                        max-height: 400px;
                        overflow-y: auto;
                    ">${data.raw_output}</pre>
                `;
            } else {
                content.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.5);">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 12px; opacity: 0.5;">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="12"/>
                            <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <div>No LLDP neighbors found</div>
                        ${data.error ? `<div style="color: #e74c3c; margin-top: 8px; font-size: 11px;">${data.error}</div>` : ''}
                        <div style="font-size: 11px; margin-top: 8px; color: rgba(255,255,255,0.4);">
                            Run "Enable LLDP" first to discover neighbors
                        </div>
                    </div>
                `;
            }
        };
        
        const lldpAbort = new AbortController();
        if (LldpDialog._lastLldpAbort) LldpDialog._lastLldpAbort.abort();
        LldpDialog._lastLldpAbort = lldpAbort;

        refreshBtn.addEventListener('click', async () => {
            if (LldpDialog._lastLldpAbort) LldpDialog._lastLldpAbort.abort();
            const refreshAbort = new AbortController();
            LldpDialog._lastLldpAbort = refreshAbort;
            refreshIcon.style.animation = 'spin 1s linear infinite';
            refreshBtn.disabled = true;
            refreshBtn.style.opacity = '0.6';
            content.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; padding: 40px; color: rgba(255,255,255,0.6);">
                    <div style="width: 20px; height: 20px; border: 2px solid rgba(0, 180, 216, 0.5); border-top-color: #00B4D8; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 12px;"></div>
                    Fetching live LLDP via SSH...
                </div>
            `;
            
            try {
                const did = device?.label || serial;
                if (window.DeviceMonitor?.refreshDevice) {
                    await window.DeviceMonitor.refreshDevice(did, true);
                    if (refreshAbort.signal.aborted) return;
                    if (device?._lldpData) {
                        updateLldpContent(device._lldpData, true);
                        editor.showToast('LLDP refreshed (live SSH)', 'success');
                    } else {
                        throw new Error('No LLDP data returned from device');
                    }
                } else {
                    const data = await self._fetchLldpNeighborsLive(serial, device, refreshAbort.signal);
                    if (refreshAbort.signal.aborted) return;
                    updateLldpContent(data);
                    editor.showToast('LLDP refreshed (live SSH)', 'success');
                }
            } catch (err) {
                if (refreshAbort.signal.aborted) return;
                content.innerHTML = `
                    <div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.5);">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="1.5" style="margin-bottom: 12px;">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <div style="color: #e74c3c;">Failed to refresh LLDP data</div>
                        <div style="margin-top: 8px; font-size: 11px;">${(err.message || 'SSH connection failed').replace(/</g, '&lt;')}</div>
                    </div>
                `;
                editor.showToast('LLDP refresh failed', 'error');
            } finally {
                refreshIcon.style.animation = '';
                refreshBtn.disabled = false;
                refreshBtn.style.opacity = '1';
            }
        });
        
        // Cache-first: if device has _lldpData, render immediately
        const hasLldpCache = device?._lldpData && (device._lldpData.neighbors?.length || device._lldpData.raw_output);
        if (hasLldpCache) {
            updateLldpContent(device._lldpData, true);
        } else {
            self._fetchLldpNeighbors(serial, device, lldpAbort.signal).then(data => {
                if (lldpAbort.signal.aborted) return;
                updateLldpContent(data);
            }).catch(err => {
                if (lldpAbort.signal.aborted) return;
                content.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: rgba(231, 76, 60, 0.9);">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom: 12px;">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        <div>Failed to load LLDP data</div>
                        <div style="font-size: 11px; margin-top: 8px; color: rgba(255,255,255,0.4);">
                            ${err.message || 'Unknown error'}
                        </div>
                    </div>
                `;
                editor.showToast('LLDP load failed', 'error');
            });
        }
    },
    
    /**
     * Detect snake patterns, DNAAS fabric, port mirror, and loop connections.
     * - Snake: ALL available NCP interfaces connecting to same neighbor (full loopback)
     * - Loop: Only SOME interfaces connecting back to same device
     * - DNAAS: Interfaces (2+) connecting to a DNAAS device (fabric uplinks)
     * - Port Mirror: Interfaces (2+) connecting to DN-LEAF device
     * @param {Array} neighbors - Array of LLDP neighbor entries
     * @param {string} deviceLabel - Current device label for loop detection
     * @param {Object} device - Device object to check total interface count
     * @returns {Array} Groups with connection type detection
     */
    _detectSnakePatterns(neighbors, deviceLabel = '', device = null) {
        const deviceLabelUpper = (deviceLabel || '').toUpperCase().replace(/[_-]/g, '');
        
        // Count total NCP interfaces on device (all ge100-* interfaces)
        let totalNcpInterfaces = 0;
        if (device && neighbors) {
            const allInterfaces = neighbors.map(n => n.interface || n.local_interface || '');
            const ncpInterfaces = allInterfaces.filter(iface => iface.match(/ge100-\d+/));
            totalNcpInterfaces = new Set(ncpInterfaces).size;
        }
        
        // Don't deduplicate - show all entries (both POVs of loop connections)
        // Deduplication for counting happens later in summary
        const workingNeighbors = neighbors;
        
        // Group by neighbor name
        const byNeighbor = {};
        workingNeighbors.forEach(n => {
            const neighbor = n.neighbor || n.neighbor_name || 'unknown';
            if (!byNeighbor[neighbor]) {
                byNeighbor[neighbor] = [];
            }
            byNeighbor[neighbor].push(n);
        });
        
        const groups = [];
        
        Object.entries(byNeighbor).forEach(([neighbor, entries]) => {
            const neighborUpper = neighbor.toUpperCase();
            const neighborNormalized = neighborUpper.replace(/[_-]/g, '');
            
            // Check connection types based on neighbor name
            const isDnaas = neighborUpper.includes('DNAAS');
            const isPortMirror = neighborUpper.includes('DN-LEAF') || neighborUpper.includes('DNLEAF');
            
            // Loop detection: neighbor matches current device (ignoring separators)
            const isSameDevice = deviceLabelUpper && (
                neighborNormalized.includes(deviceLabelUpper) || 
                deviceLabelUpper.includes(neighborNormalized.split(/\d/)[0])
            );
            
            // Count NCP interfaces in THIS group
            const ncpInterfacesInGroup = entries.filter(e => {
                const iface = e.interface || e.local_interface || '';
                return iface.match(/ge100-\d+/);
            }).length;
            
            // Snake: ALL NCP interfaces to same neighbor (not just some)
            const isSnake = isSameDevice && totalNcpInterfaces > 0 && ncpInterfacesInGroup === totalNcpInterfaces;
            
            // Loop: only SOME interfaces to same device
            const isLoop = isSameDevice && !isSnake;
            
            // Threshold: For loops, 2+ is needed for collapsible group
            // For DNAAS/Mirror: 2+, For Snake: 3+
            const minCount = isLoop ? 2 : ((isDnaas || isPortMirror) ? 2 : (isSnake ? 3 : 3));
            
            if (entries.length >= minCount) {
                // Parse interface numbers to detect sequential pattern
                const parsed = entries.map(e => {
                    const iface = e.interface || e.local_interface || '';
                    const remotePort = e.remote_port || e.neighbor_port || '';
                    // Extract numbers from interface name (e.g., "ge100-6/0/2" -> [100, 6, 0, 2])
                    const localMatch = iface.match(/(\d+)/g);
                    const remoteMatch = remotePort.match(/(\d+)/g);
                    return {
                        entry: e,
                        localIface: iface,
                        remotePort: remotePort,
                        localNums: localMatch ? localMatch.map(Number) : [],
                        remoteNums: remoteMatch ? remoteMatch.map(Number) : []
                    };
                });
                
                // Sort by last number in interface name (port number)
                parsed.sort((a, b) => {
                    const aNum = a.localNums.length > 0 ? a.localNums[a.localNums.length - 1] : 0;
                    const bNum = b.localNums.length > 0 ? b.localNums[b.localNums.length - 1] : 0;
                    return aNum - bNum;
                });
                
                // Smart range detection: find continuous sequences
                const portNumbers = parsed.map(p => p.localNums.length > 0 ? p.localNums[p.localNums.length - 1] : -1);
                
                // Helper: build compact range notation with mixed ranges and commas
                const buildSmartRange = (ports, basePrefix) => {
                    if (ports.length === 0) return '';
                    if (ports.length === 1) return `${basePrefix}${ports[0]}`;
                    
                    const parts = [];
                    let rangeStart = ports[0];
                    let prevPort = ports[0];
                    
                    for (let i = 1; i < ports.length; i++) {
                        const currentPort = ports[i];
                        
                        // Check if continuous from previous
                        if (currentPort === prevPort + 1) {
                            // Extend range
                            prevPort = currentPort;
                        } else {
                            // Break in sequence - save previous range/value
                            if (prevPort === rangeStart) {
                                // Single value
                                parts.push(rangeStart.toString());
                            } else {
                                // 2+ values - use range notation
                                parts.push(`${rangeStart}-${prevPort}`);
                            }
                            // Start new range
                            rangeStart = currentPort;
                            prevPort = currentPort;
                        }
                    }
                    
                    // Handle last range/value
                    if (prevPort === rangeStart) {
                        parts.push(rangeStart.toString());
                    } else {
                        // 2+ values - use range notation
                        parts.push(`${rangeStart}-${prevPort}`);
                    }
                    
                    return `${basePrefix}${parts.join(', ')}`;
                };
                
                // Get interface range or comma-separated list
                const firstLocal = parsed[0]?.localIface || '';
                const lastLocal = parsed[parsed.length - 1]?.localIface || '';
                const firstRemote = parsed[0]?.remotePort || '';
                const lastRemote = parsed[parsed.length - 1]?.remotePort || '';
                
                // Extract base and build smart range
                const firstMatch = firstLocal.match(/^(.+?)(\d+)$/);
                const baseLocal = firstMatch ? firstMatch[1] : '';
                const localRange = buildSmartRange(portNumbers, baseLocal);
                
                // Same for remote ports - but sort them independently
                let remotePorts = parsed.map(p => p.remoteNums.length > 0 ? p.remoteNums[p.remoteNums.length - 1] : -1);
                // Sort remote ports numerically
                remotePorts.sort((a, b) => a - b);
                const firstRemoteMatch = firstRemote.match(/^(.+?)(\d+)$/);
                const baseRemote = firstRemoteMatch ? firstRemoteMatch[1] : '';
                const remoteRange = buildSmartRange(remotePorts, baseRemote);
                
                groups.push({
                    neighbor: neighbor,
                    entries: parsed.map(p => p.entry),
                    isSnake: !isDnaas && !isPortMirror && !isLoop,  // Snake only if NOT special types
                    isDnaas: isDnaas,
                    isPortMirror: isPortMirror,
                    isLoop: isLoop,
                    localRange: localRange,
                    remoteRange: remoteRange
                });
            } else {
                // Not enough for grouping - show as regular entries
                groups.push({
                    neighbor: neighbor,
                    entries: entries,
                    isSnake: false,
                    isDnaas: isDnaas,
                    isPortMirror: isPortMirror,
                    isLoop: isLoop
                });
            }
        });
        
        // Sort groups: DNAAS first, then Port Mirror, then snakes (by size descending), then regular
        groups.sort((a, b) => {
            const aMulti = a.entries.length >= 3;
            const bMulti = b.entries.length >= 3;
            // DNAAS multi-link first
            if (a.isDnaas && aMulti && !(b.isDnaas && bMulti)) return -1;
            if (b.isDnaas && bMulti && !(a.isDnaas && aMulti)) return 1;
            // Then Port Mirror
            if (a.isPortMirror && aMulti && !(b.isPortMirror && bMulti)) return -1;
            if (b.isPortMirror && bMulti && !(a.isPortMirror && aMulti)) return 1;
            // Then snakes
            if (a.isSnake && !b.isSnake) return -1;
            if (!a.isSnake && b.isSnake) return 1;
            // Then by size
            if ((a.isSnake || a.isDnaas || a.isPortMirror) && (b.isSnake || b.isDnaas || b.isPortMirror)) {
                return b.entries.length - a.entries.length;
            }
            return 0;
        });
        
        return groups;
    },
    
    /**
     * Fetch LLDP neighbors -- cache-first via ScalerAPI.getDeviceContext (reads
     * operational.json instantly), then discovery_api as fallback.
     */
    async _fetchLldpNeighbors(serial, device = null, signal) {
        const deviceLabel = device?.label || serial;
        const sshHost = device?.sshConfig?.host || device?.sshConfig?.hostBackup || '';

        // 1. Cache-first: ScalerAPI.getDeviceContext reads operational.json
        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceContext) {
            try {
                const ctx = await ScalerAPI.getDeviceContext(deviceLabel, false, sshHost);
                if (ctx?.lldp && Array.isArray(ctx.lldp) && ctx.lldp.length > 0) {
                    return {
                        neighbors: ctx.lldp.map(n => ({
                            interface: n.local || n.interface || n.local_interface || '',
                            neighbor: n.neighbor || n.neighbor_device || n.neighbor_name || '',
                            remote_port: n.remote || n.remote_port || n.neighbor_port || ''
                        })),
                        source: 'scaler-db',
                        cached: true,
                        last_updated: ctx.last_updated || null
                    };
                }
            } catch (_) {}
        }

        // 2. Fallback: discovery_api (NetworkMapper -> SCALER DB -> inventory -> SSH)
        const url = new URL(`/api/dnaas/device/${encodeURIComponent(serial)}/lldp`, window.location.origin);
        if (sshHost && /^\d+\.\d+\.\d+\.\d+$/.test(sshHost)) {
            url.searchParams.set('ssh_host', sshHost);
        }
        try {
            const _ctrl = new AbortController();
            if (signal) signal.addEventListener('abort', () => _ctrl.abort(), { once: true });
            const _timer = setTimeout(() => _ctrl.abort(), 10000);
            const response = await fetch(url.toString(), { signal: _ctrl.signal }).finally(() => clearTimeout(_timer));
            if (response.ok) {
                return await response.json();
            }
            const errData = await response.json().catch(() => ({}));
            const msg = errData.error || errData.detail || `HTTP ${response.status}`;
            const source = errData.source ? ` (tried: ${errData.source})` : '';
            throw new Error(msg + source);
        } catch (err) {
            const m = err.message || '';
            if (m.includes('Failed to fetch') || m.includes('NetworkError')) {
                throw new Error('API unreachable - check discovery_api.py and proxy');
            }
            throw err;
        }
    },
    
    /**
     * Fetch LLDP neighbors LIVE via SSH (bypasses cache)
     * Used by refresh button to get fresh data.
     * When device has sshConfig.host, pass ssh_host so API can connect when serial does not resolve.
     */
    async _fetchLldpNeighborsLive(serial, device = null, signal) {
        const sshHost = device?.sshConfig?.host || device?.sshConfig?.hostBackup || '';
        const body = { serial };
        if (sshHost && /^\d+\.\d+\.\d+\.\d+$/.test(sshHost)) {
            body.ssh_host = sshHost;
        }
        try {
            const _ctrl = new AbortController();
            if (signal) signal.addEventListener('abort', () => _ctrl.abort(), { once: true });
            const _timer = setTimeout(() => _ctrl.abort(), 20000);
            const response = await fetch('/api/dnaas/lldp-neighbors-live', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
                signal: _ctrl.signal
            }).finally(() => clearTimeout(_timer));
            if (response.ok) {
                const data = await response.json();
                if (data.lldp_neighbors && !data.neighbors) {
                    data.neighbors = data.lldp_neighbors.map(n => ({
                        interface: n.local_interface || n.interface || '',
                        neighbor: n.neighbor_device || n.neighbor || '',
                        remote_port: n.neighbor_port || n.remote_port || ''
                    }));
                }
                data.last_updated = new Date().toISOString();
                data.cached = false;
                data.live = true;
                return data;
            }
            const errData = await response.json().catch(() => ({}));
            const msg = errData.error || errData.detail || `HTTP ${response.status}: ${response.statusText}`;
            const source = errData.source ? ` (tried: ${errData.source})` : '';
            throw new Error(msg + source);
        } catch (err) {
            const m = err.message || '';
            if (m.includes('Failed to fetch') || m.includes('NetworkError')) {
                throw new Error('Discovery API unreachable - check if serve.py and discovery_api.py are running');
            }
            if (m.includes('timeout') || m.includes('Timeout')) {
                throw new Error('Request timed out - MCP or SSH may be slow. Try cached LLDP first.');
            }
            throw err;
        }
    },
    
    /**
     * Build LLDP table HTML from snake groups
     * Extracted for reuse by refresh button
     */
    _buildLldpTableHtml(snakeGroups, data, device, deviceLabel) {
        let tableHtml = `
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead>
                    <tr style="background: rgba(255, 255, 255, 0.05);">
                        <th style="padding: 10px; text-align: left; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.1); width: 30px;"></th>
                        <th style="padding: 10px; text-align: left; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.1);">Local Interface</th>
                        <th style="padding: 10px; text-align: left; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.1);">Neighbor</th>
                        <th style="padding: 10px; text-align: left; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.1);">Remote Port</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Build table rows from snake groups
        let totalNeighbors = 0;
        let dnaasCount = 0;
        let dnaasLinkCount = 0;
        let loopCount = 0;
        let loopLinkCount = 0;
        let mirrorCount = 0;
        let mirrorLinkCount = 0;
        let snakeCount = 0;
        let snakeLinkCount = 0;
        
        // SVG icons
        const iconDnaas = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FF5E1F" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="5" r="2"/><circle cx="12" cy="19" r="2"/><circle cx="5" cy="12" r="2"/><circle cx="19" cy="12" r="2"/><line x1="12" y1="7" x2="12" y2="9"/><line x1="12" y1="15" x2="12" y2="17"/><line x1="7" y1="12" x2="9" y2="12"/><line x1="15" y1="12" x2="17" y2="12"/></svg>`;
        const iconMirror = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M7 17l-4-4 4-4"/><path d="M17 7l4 4-4 4"/><line x1="3" y1="13" x2="11" y2="13"/><line x1="13" y1="11" x2="21" y2="11"/></svg>`;
        const iconSnake = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M21 12a9 9 0 1 1-9-9"/><path d="M21 3v9h-9"/></svg>`;
        const iconLoop = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FF7A33" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="9"/><path d="M12 8v4l2 2"/></svg>`;
        
        // Helper to build a collapsible group row
        const buildCollapsibleGroup = (groupId, color, icon, localRange, remoteRange, neighbor, entryCount, label, entries) => {
            let html = `
                <tr style="background: ${color.replace(')', ', 0.08)')}; cursor: pointer;"
                        onclick="this.classList.toggle('expanded'); document.getElementById('${groupId}').style.display = this.classList.contains('expanded') ? 'table-row-group' : 'none'; this.querySelector('.group-arrow').style.transform = this.classList.contains('expanded') ? 'rotate(90deg)' : '';">
                        <td style="padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center;">
                        <span class="group-arrow" style="display: inline-block; transition: transform 0.2s; color: ${color};">&#9654;</span>
                        </td>
                    <td style="padding: 8px 10px; color: ${color}; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        ${icon}<strong>${localRange}</strong>
                        <span style="color: rgba(255,255,255,0.5); font-size: 10px; margin-left: 8px;">(${entryCount} ${label})</span>
                        </td>
                    <td style="padding: 8px 10px; color: ${color}; border-bottom: 1px solid rgba(255,255,255,0.05);"><strong>${neighbor}</strong></td>
                        <td style="padding: 8px 10px; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.05);">${remoteRange}</td>
                    </tr>
                `;
            html += `<tbody id="${groupId}" style="display: none;">`;
            entries.forEach((entry, i) => {
                const entryBg = i % 2 === 0 ? color.replace(')', ', 0.03)') : color.replace(')', ', 0.06)');
                html += `
                    <tr style="background: ${entryBg};">
                            <td style="padding: 6px 10px 6px 20px;"></td>
                        <td style="padding: 6px 10px; color: ${color.replace(')', ', 0.85)')}; border-bottom: 1px solid rgba(255,255,255,0.03);">${entry.interface || entry.local_interface || '-'}</td>
                        <td style="padding: 6px 10px; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.03);">${entry.neighbor || entry.neighbor_device || entry.neighbor_name || '-'}</td>
                            <td style="padding: 6px 10px; color: rgba(255,255,255,0.6); border-bottom: 1px solid rgba(255,255,255,0.03);">${entry.remote_port || entry.neighbor_port || '-'}</td>
                        </tr>
                    `;
                });
            html += `</tbody>`;
            return html;
        };
        
        snakeGroups.forEach((group, groupIdx) => {
            const isDnaas = group.isDnaas || group.neighbor.includes('DNAAS');
            const isLoop = group.isLoop;
            const isPortMirror = group.isPortMirror;
            const isSnake = group.isSnake;
            const isMultiLink = group.entries.length >= 2;
            const isSnakeMultiLink = group.entries.length >= 3;
            
            totalNeighbors += group.entries.length;
            
            if (isDnaas && isMultiLink) {
                dnaasCount++;
                dnaasLinkCount += group.entries.length;
                tableHtml += buildCollapsibleGroup(
                    `dnaas-${groupIdx}`, '#FF5E1F', iconDnaas,
                    group.localRange || `${group.entries.length} interfaces`,
                    group.remoteRange || `${group.entries.length} ports`,
                    group.neighbor, group.entries.length, 'DNAAS', group.entries
                );
            } else if (isPortMirror && isMultiLink) {
                mirrorCount++;
                mirrorLinkCount += group.entries.length;
                tableHtml += buildCollapsibleGroup(
                    `mirror-${groupIdx}`, 'rgba(156, 89, 182, 0.9)', iconMirror,
                    group.localRange || `${group.entries.length} interfaces`,
                    group.remoteRange || `${group.entries.length} ports`,
                    group.neighbor, group.entries.length, 'Mirror', group.entries
                );
            } else if (isLoop && isMultiLink) {
                loopCount++;
                loopLinkCount += group.entries.length;
                tableHtml += buildCollapsibleGroup(
                    `loop-${groupIdx}`, '#FF7A33', iconLoop,
                    group.localRange || `${group.entries.length} interfaces`,
                    group.remoteRange || `${group.entries.length} ports`,
                    group.neighbor, group.entries.length, 'Loop', group.entries
                );
            } else if (isSnake && isSnakeMultiLink) {
                snakeCount++;
                snakeLinkCount += group.entries.length;
                tableHtml += buildCollapsibleGroup(
                    `snake-${groupIdx}`, 'rgba(255, 193, 7, 0.9)', iconSnake,
                    group.localRange || `${group.entries.length} interfaces`,
                    group.remoteRange || `${group.entries.length} ports`,
                    group.neighbor, group.entries.length, 'Snake', group.entries
                );
            } else {
                // Regular or single-entry groups
                const icon = isDnaas ? iconDnaas : (isLoop ? iconLoop : (isPortMirror ? iconMirror : (isSnake ? iconSnake : '')));
                const color = isDnaas ? '#FF5E1F' : (isLoop ? '#FF7A33' : (isPortMirror ? 'rgba(156, 89, 182, 0.9)' : 'rgba(255,255,255,0.8)'));
                if (isDnaas) dnaasLinkCount += group.entries.length;
                if (isLoop) loopLinkCount += group.entries.length;
                if (isPortMirror) { mirrorCount++; mirrorLinkCount += group.entries.length; }
                group.entries.forEach(entry => {
                    tableHtml += `
                        <tr style="background: transparent;">
                            <td style="padding: 8px 10px; text-align: center;">${icon}</td>
                            <td style="padding: 8px 10px; color: ${color}; border-bottom: 1px solid rgba(255,255,255,0.05);">${entry.interface || entry.local_interface || '-'}</td>
                            <td style="padding: 8px 10px; color: ${color}; border-bottom: 1px solid rgba(255,255,255,0.05);">${entry.neighbor || entry.neighbor_device || entry.neighbor_name || '-'}</td>
                            <td style="padding: 8px 10px; color: rgba(255,255,255,0.7); border-bottom: 1px solid rgba(255,255,255,0.05);">${entry.remote_port || entry.neighbor_port || '-'}</td>
                        </tr>
                    `;
                });
            }
        });
        
        tableHtml += '</tbody></table>';
        
        // Summary line with counts and timestamp
        let summaryHtml = `<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);">`;
        summaryHtml += `<span style="color: rgba(255,255,255,0.6); font-size: 11px;">Found ${totalNeighbors} neighbor(s)</span>`;
        
        // Source badge + timestamp
        const srcLabels = {
            'network-mapper': 'NetworkMapper',
            'scaler-db': 'Scaler DB',
            'device-inventory': 'Inventory',
            'ssh-live': 'SSH Live',
            'unknown': 'Cache'
        };
        const srcLabel = srcLabels[data.source] || (data.cached ? 'Cache' : 'Live');
        const srcColor = data.source === 'network-mapper' ? '#2ecc71' : 
                         data.source === 'ssh-live' ? '#3498db' : 'rgba(255,255,255,0.5)';
        
        let timestampStr = '';
        if (data.last_updated) {
            const timestamp = new Date(data.last_updated);
            if (!isNaN(timestamp.getTime())) {
                const timeStr = timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
                const dateStr = timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                timestampStr = `${dateStr} ${timeStr}`;
            } else {
                timestampStr = data.last_updated;
            }
        } else if (device?._lldpCompletedAt) {
            const timestamp = new Date(device._lldpCompletedAt);
            const timeStr = timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
            const dateStr = timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            timestampStr = `${dateStr} ${timeStr}`;
        }
        
        summaryHtml += `<span style="color: rgba(255,255,255,0.4); font-size: 10px; margin-left: auto;">`;
        if (timestampStr) summaryHtml += `Last scan: ${timestampStr} `;
        summaryHtml += `<span style="color: ${srcColor}; font-weight: 600; padding: 1px 5px; border-radius: 3px; background: rgba(255,255,255,0.06); font-size: 9px;">${srcLabel}</span>`;
        summaryHtml += `</span>`;
        
        if (dnaasLinkCount > 0) {
            summaryHtml += `<span style="color: #FF5E1F; display: inline-flex; align-items: center; gap: 3px;">${iconDnaas}${dnaasCount || 1} DNAAS (${dnaasLinkCount})</span>`;
        }
        if (mirrorLinkCount > 0) {
            summaryHtml += `<span style="color: rgba(156, 89, 182, 0.9); display: inline-flex; align-items: center; gap: 3px;">${iconMirror}${mirrorCount} Mirror (${mirrorLinkCount})</span>`;
        }
        if (loopLinkCount > 0) {
            summaryHtml += `<span style="color: #FF7A33; display: inline-flex; align-items: center; gap: 3px;">${iconLoop}${loopCount || 1} Loop (${loopLinkCount})</span>`;
        }
        if (snakeLinkCount > 0) {
            summaryHtml += `<span style="color: rgba(255, 193, 7, 0.9); display: inline-flex; align-items: center; gap: 3px;">${iconSnake}${snakeCount} Snake (${snakeLinkCount})</span>`;
        }
        summaryHtml += '</div>';
        
        return summaryHtml + tableHtml;
    },
    
    /**
     * Attach event handlers to LLDP table rows for expand/collapse
     */
    _attachLldpTableEvents(content, device, snakeGroups, dialog) {
        // Add expand/collapse behavior for snake groups
        content.querySelectorAll('.snake-group-header').forEach(header => {
            header.addEventListener('click', () => {
                const groupIdx = header.dataset.group;
                const entries = content.querySelectorAll(`.snake-group-entry[data-group="${groupIdx}"]`);
                const isExpanded = entries[0]?.style.display !== 'none';
                entries.forEach(entry => {
                    entry.style.display = isExpanded ? 'none' : 'table-row';
                });
                // Update expand icon
                const icon = header.querySelector('td:first-child');
                if (icon) {
                    const group = snakeGroups[parseInt(groupIdx)];
                    const isDnaas = group?.neighbor?.includes('DNAAS') || group?.neighbor?.includes('LEAF') || group?.neighbor?.includes('SPINE');
                    const isLoop = group?.isLoop;
                    icon.textContent = isLoop ? '⏺' : (isDnaas ? '⚙️' : (isExpanded ? '▼' : '▶'));
                }
            });
        });
    },
    
    /**
     * Show LLDP button menu with options: Enable LLDP, LLDP Table
     * Uses Liquid Glass styling matching parent toolbar
     */
    showLldpButtonMenu(editor, device, x, y) {
        // Remove any existing menu
        const existing = document.getElementById('lldp-button-menu');
        if (existing) existing.remove();
        
        // Get serial for API calls - PREFER sshConfig.host (actual address) over label
        const serial = device?.sshConfig?.host || device?.deviceSerial || device?.label || '';
        console.log('LLDP menu - device:', device?.label, 'serial/host for API:', serial);
        
        // Liquid Glass styling (mode-aware)
        const isDarkMode = editor.darkMode;
        const glassBg = isDarkMode 
            ? 'linear-gradient(135deg, rgba(25, 30, 42, 0.92) 0%, rgba(18, 22, 35, 0.95) 100%)' 
            : 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(245, 248, 255, 0.92) 100%)';
        const glassBorder = isDarkMode ? 'rgba(100, 150, 255, 0.18)' : 'rgba(100, 150, 200, 0.25)';
        const glassShadow = isDarkMode 
            ? '0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
            : '0 8px 32px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.8)';
        const textColor = isDarkMode ? 'rgba(255, 255, 255, 0.9)' : 'rgba(30, 30, 50, 0.9)';
        const hoverBg = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)';
        const accentColor = '#00B4D8';
        
        // Create menu container
        const menu = document.createElement('div');
        menu.id = 'lldp-button-menu';
        menu.style.cssText = `
            position: fixed;
            z-index: 10001;
            min-width: 180px;
            background: ${glassBg};
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid ${glassBorder};
            border-radius: 12px;
            box-shadow: ${glassShadow};
            padding: 6px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        
        // Option styling (Liquid Glass, mode-aware)
        const createOption = (icon, label, onClick, isActive = false) => {
            const option = document.createElement('div');
            option.style.cssText = `
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 14px;
                color: ${isActive ? accentColor : textColor};
                font-size: 13px;
                cursor: pointer;
                border-radius: 8px;
                transition: all 0.15s ease;
                background: ${isActive ? (isDarkMode ? 'rgba(0, 180, 216, 0.15)' : 'rgba(0, 180, 216, 0.1)') : 'transparent'};
            `;
            option.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${icon}
                </svg>
                <span>${label}</span>
            `;
            option.addEventListener('mouseenter', () => {
                option.style.background = hoverBg;
            });
            option.addEventListener('mouseleave', () => {
                option.style.background = isActive ? (isDarkMode ? 'rgba(0, 180, 216, 0.15)' : 'rgba(0, 180, 216, 0.1)') : 'transparent';
            });
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.remove();
                onClick();
            });
            return option;
        };
        
        const hasLldpData = device?.lldpEnabled || device?.lldpDiscoveryComplete;
        const hasNewResults = device?._lldpNewResults;
        const isLldpRunning = device?._lldpRunning || device?._lldpAnimating;
        
        if (isLldpRunning) {
            // Running state - show with spinner indicator
            const runningOption = document.createElement('div');
            runningOption.style.cssText = `
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 14px;
                color: ${accentColor};
                font-size: 13px;
                cursor: default;
                border-radius: 8px;
                background: ${isDarkMode ? 'rgba(0, 180, 216, 0.15)' : 'rgba(0, 180, 216, 0.1)'};
            `;
            runningOption.innerHTML = `
                <div style="width: 16px; height: 16px; border: 2px solid rgba(0, 180, 216, 0.3); border-top-color: ${accentColor}; border-radius: 50%; animation: lldpMenuSpin 0.8s linear infinite;"></div>
                <span>LLDP Running...</span>
            `;
            // Add animation keyframes
            if (!document.getElementById('lldp-menu-spin-style')) {
                const style = document.createElement('style');
                style.id = 'lldp-menu-spin-style';
                style.textContent = `@keyframes lldpMenuSpin { to { transform: rotate(360deg); } }`;
                document.head.appendChild(style);
            }
            menu.appendChild(runningOption);
        } else {
            // Normal state - Enable LLDP option
            menu.appendChild(createOption(
                '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
                hasLldpData ? 'LLDP enabled (re-scan)' : 'Enable LLDP',
                () => {
                    if (serial) {
                        editor.enableLldpBackground(device, serial, device?.sshConfig);
                    } else {
                        editor.showToast('No SSH address configured', 'error');
                    }
                },
                hasNewResults
            ));
        }
        
        // LLDP Table option
        menu.appendChild(createOption(
            '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
            'LLDP Table',
            () => {
                this.showLldpTableDialog(editor, device, serial);
            },
            hasNewResults
        ));
        
        // System Stack option
        menu.appendChild(createOption(
            '<rect x="4" y="4" width="16" height="4" rx="1"/><rect x="4" y="10" width="16" height="4" rx="1"/><rect x="4" y="16" width="16" height="4" rx="1"/>',
            'System Stack',
            () => {
                if (editor.showSystemStackDialog) {
                    editor.showSystemStackDialog(device, serial);
                }
            }
        ));
        
        menu.addEventListener('keydown', (e) => { e.stopPropagation(); });
        menu.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(menu);
        
        // Position menu, keeping within viewport
        const menuRect = menu.getBoundingClientRect();
        const padding = 10;
        let menuX = x;
        let menuY = y;
        
        if (menuX + menuRect.width > window.innerWidth - padding) {
            menuX = window.innerWidth - menuRect.width - padding;
        }
        if (menuX < padding) menuX = padding;
        
        if (menuY + menuRect.height > window.innerHeight - padding) {
            menuY = y - menuRect.height; // Show above
        }
        if (menuY < padding) menuY = padding;
        
        menu.style.left = menuX + 'px';
        menu.style.top = menuY + 'px';
        
        // Close on click outside
        const closeHandler = (e) => {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeHandler);
            }
        };
        setTimeout(() => document.addEventListener('click', closeHandler), 10);
    },

    /**
     * Show Enable LLDP dialog for a device
     * Extracted from topology.js for modular architecture
     */
    showEnableLldpDialog(editor, serial, sshConfig = {}) {
        // Store sshConfig for use in the enable handler
        editor._lldpSshConfig = sshConfig;
        
        // Hide device toolbar to avoid overlap
        editor.hideDeviceSelectionToolbar();
        
        // Liquid Glass styling
        const isDarkMode = editor.darkMode;
        const glassBg = isDarkMode 
            ? 'linear-gradient(135deg, rgba(20, 25, 40, 0.92) 0%, rgba(15, 20, 35, 0.95) 100%)' 
            : 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 245, 255, 0.92) 100%)';
        const glassBorder = isDarkMode ? 'rgba(100, 180, 255, 0.2)' : 'rgba(100, 150, 200, 0.25)';
        const glassShadow = isDarkMode 
            ? '0 20px 60px rgba(0, 0, 0, 0.5), 0 8px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
            : '0 20px 60px rgba(0, 0, 0, 0.15), 0 8px 24px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.8)';
        const textColor = isDarkMode ? '#ecf0f1' : '#1a1a2e';
        const subtleText = isDarkMode ? '#95a5a6' : '#666';
        const accentColor = '#00B4D8';
        const infoBg = isDarkMode ? 'rgba(0, 180, 216, 0.1)' : 'rgba(0, 180, 216, 0.08)';
        const infoBorder = isDarkMode ? 'rgba(0, 180, 216, 0.25)' : 'rgba(0, 180, 216, 0.3)';
        const btnBg = isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
        const btnBorder = isDarkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)';
        
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.id = 'enable-lldp-dialog-overlay';
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: ${isDarkMode ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.3)'};
            display: flex; align-items: center; justify-content: center;
            z-index: 100000; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
        `;
        
        // Create dialog
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: ${glassBg}; border-radius: 16px; border: 1px solid ${glassBorder};
            padding: 24px; max-width: 450px; width: 90%; box-shadow: ${glassShadow};
            backdrop-filter: blur(32px) saturate(180%); -webkit-backdrop-filter: blur(32px) saturate(180%);
            animation: lldpDialogIn 0.2s ease;
        `;
        
        // Add animation styles
        if (!document.getElementById('lldp-dialog-styles')) {
            const style = document.createElement('style');
            style.id = 'lldp-dialog-styles';
            style.textContent = `
                @keyframes lldpDialogIn { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
                @keyframes spin { to { transform: rotate(360deg); } }
            `;
            document.head.appendChild(style);
        }
        
        dialog.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <div style="width: 36px; height: 36px; background: linear-gradient(135deg, ${accentColor}, #0096B4); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </div>
                <h3 style="margin: 0; color: ${textColor}; font-size: 17px; font-weight: 600;">Enable LLDP on Device</h3>
            </div>
            <p style="color: ${subtleText}; font-size: 13px; line-height: 1.6; margin-bottom: 18px;">
                This will enable LLDP on all <strong style="color: ${accentColor};">physical interfaces</strong> 
                of device <strong style="color: #FF7A33;">${serial}</strong>.
            </p>
            <div style="background: ${infoBg}; border: 1px solid ${infoBorder}; border-radius: 10px; padding: 14px; margin-bottom: 18px;">
                <div style="color: ${accentColor}; font-weight: 600; margin-bottom: 8px; font-size: 11px; text-transform: uppercase;">What this does:</div>
                <ul style="margin: 0; padding-left: 18px; color: ${subtleText}; font-size: 12px; line-height: 1.9;">
                    <li>Enables global LLDP protocol</li>
                    <li>Sets admin-state enabled on all ge*/xe* interfaces</li>
                    <li>Commits the configuration</li>
                </ul>
            </div>
            <div id="lldp-status" style="display: none; padding: 12px 14px; border-radius: 10px; margin-bottom: 16px; font-size: 13px;"></div>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button id="lldp-cancel-btn" style="padding: 10px 18px; background: ${btnBg}; border: 1px solid ${btnBorder}; border-radius: 8px; color: ${subtleText}; cursor: pointer; font-size: 13px;">Cancel</button>
                <button id="lldp-enable-btn" style="padding: 10px 20px; background: linear-gradient(135deg, ${accentColor}, #0096B4); border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: 600; font-size: 13px; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 8px rgba(0, 180, 216, 0.3);">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>Enable LLDP
                </button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        overlay.addEventListener('keydown', (e) => { e.stopPropagation(); });
        overlay.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(overlay);
        
        const statusDiv = dialog.querySelector('#lldp-status');
        const enableBtn = dialog.querySelector('#lldp-enable-btn');
        const cancelBtn = dialog.querySelector('#lldp-cancel-btn');
        
        cancelBtn.onclick = () => overlay.remove();
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
        
        enableBtn.onclick = async () => {
            enableBtn.disabled = true;
            enableBtn.innerHTML = `<div style="width: 14px; height: 14px; border: 2px solid white; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>Enabling...`;
            cancelBtn.disabled = true;
            
            statusDiv.style.display = 'block';
            statusDiv.style.background = 'rgba(255, 94, 31, 0.1)';
            statusDiv.style.border = '1px solid rgba(255, 94, 31, 0.3)';
            statusDiv.style.color = '#FF7A33';
            statusDiv.textContent = 'Connecting to device and enabling LLDP...';
            
            try {
                const result = await editor._enableLldpOnDevice(serial, editor._lldpSshConfig || {});
                
                if (result.success) {
                    statusDiv.style.background = 'rgba(39, 174, 96, 0.1)';
                    statusDiv.style.border = '1px solid rgba(39, 174, 96, 0.3)';
                    statusDiv.style.color = '#27ae60';
                    
                    if (result.already_configured) {
                        statusDiv.innerHTML = `<div style="font-weight: 600;">✓ LLDP Already Configured!</div><div>All interfaces already have LLDP enabled</div>`;
                        editor.showToast('LLDP already configured! Ready for discovery.', 'success');
                    } else {
                        statusDiv.innerHTML = `<div style="font-weight: 600;">✓ LLDP Enabled Successfully!</div><div>Enabled on ${result.interfaces_enabled || 'all'} interfaces</div>`;
                        editor.showToast('LLDP enabled! Wait 30 seconds then run discovery.', 'success');
                    }
                    setTimeout(() => overlay.remove(), 3000);
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
            } catch (error) {
                statusDiv.style.background = 'rgba(231, 76, 60, 0.1)';
                statusDiv.style.border = '1px solid rgba(231, 76, 60, 0.3)';
                statusDiv.style.color = '#e74c3c';
                statusDiv.innerHTML = `<div style="font-weight: 600;">✗ Failed to enable LLDP</div><div style="margin-top: 4px;">${error.message}</div>`;
                enableBtn.disabled = false;
                enableBtn.innerHTML = 'Retry';
                cancelBtn.disabled = false;
            }
        };
    }

};

console.log('[topology-lldp-dialog.js] LldpDialog loaded');
