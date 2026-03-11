/**
 * topology-dnaas-operations.js - DNAAS Operations Module
 * 
 * Extracted from topology.js for modular architecture.
 * Contains DNAAS layout, loading, and BD visibility functions.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.DnaasOperations = {

    // =========================================================================
    // LAYOUT HELPER FUNCTIONS
    // =========================================================================

    /**
     * Calculate the display width of a device label for spacing calculations
     * @param {string} label - Device label
     * @returns {number} Approximate width in pixels
     */
    calculateLabelWidth(label) {
        if (!label) return 100;
        const charWidth = 9;
        const iconBuffer = 70;
        return Math.max(120, label.length * charWidth + iconBuffer * 2);
    },

    /**
     * Calculate minimum spacing needed for a row of devices based on their labels
     * @param {Object} editor - TopologyEditor instance
     * @param {Array} devices - Array of device objects
     * @param {number} minSpacing - Minimum spacing value
     * @returns {number} Calculated spacing
     */
    calculateRowSpacing(editor, devices, minSpacing = 160) {
        if (devices.length <= 1) return minSpacing;
        
        let maxLabelWidth = 0;
        devices.forEach(device => {
            const labelWidth = this.calculateLabelWidth(device.label);
            if (labelWidth > maxLabelWidth) maxLabelWidth = labelWidth;
        });
        
        const labelPadding = 40;
        return Math.max(minSpacing, maxLabelWidth + labelPadding);
    },

    /**
     * Sort devices by their label suffix for logical ordering
     * @param {Array} devices - Array of device objects
     * @returns {Array} Sorted devices
     */
    sortDevicesByLabel(devices) {
        return devices.sort((a, b) => {
            const labelA = a.label || '';
            const labelB = b.label || '';
            
            const suffixA = labelA.split(/[-_]/).pop() || labelA;
            const suffixB = labelB.split(/[-_]/).pop() || labelB;
            
            return suffixA.localeCompare(suffixB, undefined, { numeric: true, sensitivity: 'base' });
        });
    },

    // =========================================================================
    // BD VISIBILITY FUNCTIONS
    // =========================================================================

    /**
     * Toggle visibility of a specific Bridge Domain
     * @param {Object} editor - TopologyEditor instance
     * @param {string} bdName - Bridge Domain name
     * @param {boolean} visible - Visibility state
     */
    toggleBDVisibility(editor, bdName, visible) {
        if (!editor._bdVisibility) editor._bdVisibility = {};
        editor._bdVisibility[bdName] = visible;
        
        // Update link visibility
        editor.objects.forEach(obj => {
            if (obj.type === 'link') {
                const linkBdName = obj.linkDetails?.bd_name || obj._bdName;
                if (linkBdName === bdName) {
                    obj._hidden = !visible;
                }
            }
        });
        
        // Update device visibility
        this._updateDeviceVisibilityByBD(editor);
        
        // Save state
        this._saveBDPanelState(editor);
        
        editor.draw();
    },

    /**
     * Update device visibility based on BD visibility states
     * @param {Object} editor - TopologyEditor instance
     */
    _updateDeviceVisibilityByBD(editor) {
        if (!editor._bdVisibility) return;
        
        const deviceBDs = {};
        
        editor.objects.forEach(obj => {
            if (obj.type === 'link' || obj.type === 'unbound') {
                const bdName = obj.linkDetails?.bd_name || obj._bdName;
                if (!bdName) return;
                
                let device1, device2;
                if (obj.device1) {
                    device1 = editor.objects.find(d => d.id === obj.device1);
                }
                if (obj.device2) {
                    device2 = editor.objects.find(d => d.id === obj.device2);
                }
                
                if (device1 && device1.type === 'device') {
                    if (!deviceBDs[device1.id]) deviceBDs[device1.id] = new Set();
                    deviceBDs[device1.id].add(bdName);
                }
                if (device2 && device2.type === 'device') {
                    if (!deviceBDs[device2.id]) deviceBDs[device2.id] = new Set();
                    deviceBDs[device2.id].add(bdName);
                }
            }
        });
        
        // Update device visibility
        editor.objects.forEach(obj => {
            if (obj.type !== 'device') return;
            
            const bds = deviceBDs[obj.id];
            if (!bds || bds.size === 0) {
                obj._hidden = false;
                return;
            }
            
            const hasVisibleBD = Array.from(bds).some(bd => editor._bdVisibility[bd] !== false);
            obj._hidden = !hasVisibleBD;
        });
        
        // Update text visibility
        editor.objects.forEach(obj => {
            if (obj.type !== 'text') return;
            
            if (obj.attachedToLink) {
                const attachedLink = editor.objects.find(l => l.id === obj.attachedToLink);
                if (attachedLink) {
                    obj._hidden = attachedLink._hidden;
                }
            }
        });
    },

    /**
     * Save BD panel state to localStorage
     * @param {Object} editor - TopologyEditor instance
     */
    _saveBDPanelState(editor) {
        if (!editor._bdVisibility) return;
        
        const state = {
            visibility: editor._bdVisibility,
            panelOpen: editor._bdPanelOpen !== false,
            viewMode: editor._bdViewMode || 'normal'
        };
        
        try {
            localStorage.setItem('topology_bd_panel_state', JSON.stringify(state));
        } catch (e) {
            console.warn('Could not save BD panel state:', e);
        }
    },

    /**
     * Set visibility for all Bridge Domains
     * @param {Object} editor - TopologyEditor instance
     * @param {boolean} visible - Visibility state
     */
    setBDVisibilityAll(editor, visible) {
        if (!editor._multiBDMetadata || !editor._multiBDMetadata.bridge_domains) return;
        
        if (!editor._bdVisibility) editor._bdVisibility = {};
        
        editor._multiBDMetadata.bridge_domains.forEach(bd => {
            editor._bdVisibility[bd.name] = visible;
        });
        
        // Update all links
        editor.objects.forEach(obj => {
            if (obj.type === 'link') {
                const bdName = obj.linkDetails?.bd_name || obj._bdName;
                if (bdName) {
                    obj._hidden = !visible;
                }
            }
        });
        
        this._updateDeviceVisibilityByBD(editor);
        this._saveBDPanelState(editor);
        
        // Update legend checkboxes
        const checkboxes = document.querySelectorAll('.bd-legend-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = visible;
        });
        
        editor.draw();
    },

    /**
     * Hide the BD Legend panel
     * @param {Object} editor - TopologyEditor instance
     */
    hideBDLegend(editor) {
        const existingPanel = document.getElementById('bd-legend-panel');
        if (existingPanel) {
            existingPanel.remove();
        }
        editor._bdPanelOpen = false;
        this._saveBDPanelState(editor);
    },

    /**
     * Toggle the BD Legend panel visibility
     * @param {Object} editor - TopologyEditor instance
     */
    toggleBDLegendPanel(editor) {
        const panel = document.getElementById('bd-legend-panel');

        if (panel) {
            const isVisible = panel.style.display !== 'none';
            if (isVisible) {
                editor.hideBDLegend();
            } else {
                panel.style.display = 'block';
                editor._bdPanelOpen = true;
            }
            editor._saveBDPanelState();
            editor.updateBDHierarchyButton();
            return;
        }

        if (!editor._multiBDMetadata || !editor._multiBDMetadata.bridge_domains || editor._multiBDMetadata.bridge_domains.length === 0) {
            DnaasOperations._reconstructBDMetadataFromCanvas(editor);
        }

        if (editor._multiBDMetadata && editor._multiBDMetadata.bridge_domains && editor._multiBDMetadata.bridge_domains.length > 0) {
            editor.showBDLegend(editor._multiBDMetadata.bridge_domains);
            editor.updateBDHierarchyButton();
        } else {
            editor.showToast('No Bridge Domains on canvas. Run DNAAS discovery first.', 'warning');
        }
    },

    _reconstructBDMetadataFromCanvas(editor) {
        const BD_COLOR_PALETTE = [
            '#00bcd4', '#ff9800', '#4caf50', '#e91e63', '#9c27b0',
            '#03a9f4', '#ff5722', '#8bc34a', '#673ab7', '#ffc107',
            '#009688', '#f44336', '#2196f3', '#cddc39', '#ff6f00'
        ];
        const seen = new Map();
        editor.objects.forEach(obj => {
            if (obj.type !== 'link' && obj.type !== 'unbound') return;
            const bdName = obj.linkDetails?.bd_name || obj._bdName;
            if (!bdName || seen.has(bdName)) return;
            const vlan = obj.linkDetails?.vlan || obj.linkDetails?.vlan_id || obj.linkDetails?.global_vlan || null;
            seen.set(bdName, { name: bdName, vlan: vlan });
        });
        if (seen.size === 0) return;
        const bds = [];
        let idx = 0;
        for (const [name, info] of seen) {
            bds.push({ name, bd_name: name, vlan: info.vlan, color: BD_COLOR_PALETTE[idx % BD_COLOR_PALETTE.length] });
            idx++;
        }
        editor._multiBDMetadata = { bridge_domains: bds, view_mode: 'separate' };
    },

    /**
     * Update the BD Hierarchy button visibility
     * @param {Object} editor - TopologyEditor instance
     */
    updateBDHierarchyButton(editor) {
        const btnHierarchy = document.getElementById('btn-bd-hierarchy');
        if (!btnHierarchy) return;
        
        const hasMultiBD = editor._multiBDMetadata && 
                           editor._multiBDMetadata.bridge_domains && 
                           editor._multiBDMetadata.bridge_domains.length > 0;
        
        if (hasMultiBD) {
            btnHierarchy.style.display = 'flex';
            btnHierarchy.title = `BD Hierarchy (${editor._multiBDMetadata.bridge_domains.length} BDs)`;
        } else {
            btnHierarchy.style.display = 'none';
        }
    },

    /**
     * Restore BD panel if it was open before refresh
     * @param {Object} editor - TopologyEditor instance
     */
    restoreBDPanelIfNeeded(editor) {
        try {
            const savedState = localStorage.getItem('topology_bd_panel_state');
            if (!savedState) return;
            
            const state = JSON.parse(savedState);
            
            if (state.visibility) {
                editor._bdVisibility = state.visibility;
            }
            
            if (state.viewMode) {
                editor._bdViewMode = state.viewMode;
            }
            
            // Restore visibility to objects
            editor.objects.forEach(obj => {
                if (obj.type === 'link') {
                    const bdName = obj.linkDetails?.bd_name || obj._bdName;
                    if (bdName && editor._bdVisibility) {
                        obj._hidden = editor._bdVisibility[bdName] === false;
                    }
                }
            });
            
            this._updateDeviceVisibilityByBD(editor);
            
            editor._bdPanelOpen = state.panelOpen !== false;
            
        } catch (e) {
            console.warn('Could not restore BD panel state:', e);
        }
    },

    /**
     * Toggle between link view modes
     * @param {Object} editor - TopologyEditor instance
     */
    toggleBDLinkView(editor) {
        const modes = ['normal', 'compact', 'lines-only'];
        const currentIndex = modes.indexOf(editor._bdViewMode || 'normal');
        const nextIndex = (currentIndex + 1) % modes.length;
        editor._bdViewMode = modes[nextIndex];
        
        this.applyBDViewMode(editor, editor._bdViewMode);
        this._saveBDPanelState(editor);
    },

    /**
     * Apply a specific BD view mode
     * @param {Object} editor - TopologyEditor instance
     * @param {string} mode - View mode
     */
    applyBDViewMode(editor, mode) {
        editor._bdViewMode = mode;
        
        switch (mode) {
            case 'compact':
                editor.objects.forEach(obj => {
                    if (obj.type === 'link') {
                        obj._compactView = true;
                    }
                });
                break;
            case 'lines-only':
                editor.objects.forEach(obj => {
                    if (obj.type === 'link') {
                        obj._linesOnlyView = true;
                        obj._compactView = false;
                    }
                });
                break;
            default:
                editor.objects.forEach(obj => {
                    if (obj.type === 'link') {
                        obj._compactView = false;
                        obj._linesOnlyView = false;
                    }
                });
        }
        
        editor.draw();
    },

    /**
     * Highlight links belonging to a specific Bridge Domain
     * @param {Object} editor - TopologyEditor instance
     * @param {string} bdName - Bridge Domain name
     */
    highlightBDPath(editor, bdName) {
        // Reset all link highlights
        editor.objects.forEach(obj => {
            if (obj.type === 'link') {
                obj._highlighted = false;
            }
        });
        
        // Highlight links for this BD
        if (bdName) {
            editor.objects.forEach(obj => {
                if (obj.type === 'link') {
                    const linkBd = obj.linkDetails?.bd_name || obj._bdName;
                    if (linkBd === bdName) {
                        obj._highlighted = true;
                    }
                }
            });
        }
        
        editor.draw();
    },

    /**
     * Create a BD Text Box for the legend area
     * @param {Object} bd - Bridge Domain object
     * @param {number} colorIndex - Color palette index
     * @returns {Object} Text object
     */
    createBDTextBox(bd, colorIndex) {
        const BD_COLOR_PALETTE = [
            '#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#f39c12',
            '#1ABC9C', '#E91E63', '#00BCD4', '#FF5722', '#8BC34A'
        ];
        
        const color = bd.color || BD_COLOR_PALETTE[colorIndex % BD_COLOR_PALETTE.length];
        
        return {
            id: `bd_text_${colorIndex}`,
            type: 'text',
            x: 80,
            y: 100 + colorIndex * 70,
            text: `${bd.name}\nType: ${bd.type || 'Unknown'}\nVLAN: ${bd.vlan || bd.global_vlan || 'N/A'}`,
            fontSize: 12,
            color: color,
            rotation: 0,
            showBackground: true,
            backgroundColor: color + '20',
            backgroundOpacity: 90,
            strokeColor: color,
            strokeWidth: 1
        };
    },

    /**
     * Apply hierarchical tree layout to DNAAS devices
     * Extracted from topology.js for modular architecture
     */
    applyDnaasHierarchicalLayout(editor, objects) {
        const devices = objects.filter(o => o.type === 'device');
        const links = objects.filter(o => o.type === 'link' || o.type === 'unbound');
        if (devices.length === 0) return;
        
        console.log(`[DNAAS Layout] Starting hierarchical layout for ${devices.length} devices, ${links.length} links`);
        
        // Categorize devices by role
        const categories = { superSpine: [], spine: [], leaf: [], pe: [], other: [] };
        const deviceById = {};
        const deviceByLabel = {};
        
        devices.forEach(device => {
            deviceById[device.id] = device;
            if (device.label) {
                deviceByLabel[device.label] = device;
                deviceByLabel[device.label.toUpperCase()] = device;
            }
        });
        
        devices.forEach(device => {
            const label = (device.label || '').toUpperCase();
            if (label.includes('SUPERSPINE') || label.includes('SUPER-SPINE') || label.includes('SS-')) {
                categories.superSpine.push(device);
            } else if ((label.includes('SPINE') && !label.includes('SUPERSPINE')) || label.match(/SPINE[-_]?[A-Z]?\d/i)) {
                categories.spine.push(device);
            } else if (label.includes('LEAF') || label.includes('TOR') || label.includes('ACCESS')) {
                categories.leaf.push(device);
            } else if (label.includes('DNAAS') && !label.includes('SPINE') && !label.includes('LEAF')) {
                categories.other.push(device);
            } else {
                categories.pe.push(device);
            }
        });
        
        // Re-categorize based on connections
        if (links.length > 0) {
            const leafIds = new Set(categories.leaf.map(d => d.id));
            const spineIds = new Set(categories.spine.map(d => d.id));
            const ssIds = new Set(categories.superSpine.map(d => d.id));
            
            const getConnectionProfile = (device) => {
                const connections = links.filter(l => l.device1 === device.id || l.device2 === device.id);
                let connectsToLeaf = false, connectsToSpine = false, connectsToSS = false;
                connections.forEach(link => {
                    const otherId = link.device1 === device.id ? link.device2 : link.device1;
                    if (leafIds.has(otherId)) connectsToLeaf = true;
                    if (spineIds.has(otherId)) connectsToSpine = true;
                    if (ssIds.has(otherId)) connectsToSS = true;
                });
                return { connectsToLeaf, connectsToSpine, connectsToSS };
            };
            
            // Re-categorize "other" devices
            const toReclassifyOther = [...categories.other];
            categories.other = [];
            toReclassifyOther.forEach(device => {
                const { connectsToLeaf, connectsToSpine, connectsToSS } = getConnectionProfile(device);
                if (connectsToSS && !connectsToLeaf && !connectsToSpine) categories.superSpine.push(device);
                else if (connectsToSS && !connectsToLeaf) categories.spine.push(device);
                else if (connectsToSpine && !connectsToLeaf) categories.spine.push(device);
                else if (connectsToLeaf) categories.pe.push(device);
                else categories.other.push(device);
            });
            
            // Re-categorize PE devices connecting to SuperSpine
            const toReclassifyPE = [...categories.pe];
            categories.pe = [];
            toReclassifyPE.forEach(device => {
                const { connectsToLeaf, connectsToSpine, connectsToSS } = getConnectionProfile(device);
                if (connectsToSS && !connectsToLeaf && !connectsToSpine) categories.superSpine.push(device);
                else if (connectsToSS && !connectsToLeaf) categories.spine.push(device);
                else categories.pe.push(device);
            });
        }
        
        // Sort categories
        const sortByLabel = (a, b) => (a.label || '').localeCompare(b.label || '', undefined, { numeric: true });
        Object.keys(categories).forEach(key => categories[key].sort(sortByLabel));
        
        // Build connection maps
        const leafIds = new Set(categories.leaf.map(l => l.id));
        const peIds = new Set(categories.pe.map(p => p.id));
        const peToLeafConnections = {};
        
        links.forEach(link => {
            const dev1Id = link.device1, dev2Id = link.device2;
            if (peIds.has(dev1Id) && leafIds.has(dev2Id)) {
                if (!peToLeafConnections[dev1Id]) peToLeafConnections[dev1Id] = [];
                peToLeafConnections[dev1Id].push(deviceById[dev2Id]);
            } else if (peIds.has(dev2Id) && leafIds.has(dev1Id)) {
                if (!peToLeafConnections[dev2Id]) peToLeafConnections[dev2Id] = [];
                peToLeafConnections[dev2Id].push(deviceById[dev1Id]);
            }
        });
        
        // Calculate layout dimensions
        const tierCounts = {
            superSpine: categories.superSpine.length, spine: categories.spine.length,
            leaf: categories.leaf.length, pe: categories.pe.length, other: categories.other.length
        };
        const maxTierCount = Math.max(...Object.values(tierCounts), 1);
        const baseSpacing = 320;
        const globalWidth = maxTierCount * baseSpacing;
        const canvasWidth = Math.max(2000, globalWidth + 600);
        const fabricCenterX = canvasWidth / 2;
        const tierSpacing = 280;
        const startY = 200;
        
        // Layout function
        const layoutTierSymmetric = (deviceList, y, tierName) => {
            if (deviceList.length === 0) return;
            const count = deviceList.length;
            let spacing;
            if (count === 1) spacing = 0;
            else if (count <= 3) spacing = baseSpacing * 1.2;
            else if (count <= maxTierCount) spacing = Math.min(baseSpacing * 1.1, globalWidth / (count - 1));
            else spacing = baseSpacing;
            
            const tierWidth = (count - 1) * spacing;
            const startX = fabricCenterX - tierWidth / 2;
            deviceList.forEach((device, i) => { device.x = startX + i * spacing; device.y = y; });
            console.log(`[DNAAS Layout] ${tierName}: ${count} devices, spacing=${Math.round(spacing)}px`);
        };
        
        // Apply layout to all tiers
        let currentY = startY;
        if (categories.superSpine.length > 0) { layoutTierSymmetric(categories.superSpine, currentY, 'SuperSpine'); currentY += tierSpacing; }
        if (categories.spine.length > 0) { layoutTierSymmetric(categories.spine, currentY, 'Spine'); currentY += tierSpacing; }
        if (categories.leaf.length > 0) { layoutTierSymmetric(categories.leaf, currentY, 'Leaf'); currentY += tierSpacing; }
        
        if (categories.pe.length > 0) {
            // Position each PE directly under the centroid of its connected LEAFs
            const positioned = [];
            const unconnected = [];
            
            categories.pe.forEach(pe => {
                const connectedLeafs = peToLeafConnections[pe.id];
                if (connectedLeafs && connectedLeafs.length > 0) {
                    const avgX = connectedLeafs.reduce((sum, leaf) => sum + (leaf.x || fabricCenterX), 0) / connectedLeafs.length;
                    pe.x = avgX;
                    pe.y = currentY;
                    positioned.push(pe);
                } else {
                    unconnected.push(pe);
                }
            });
            
            // Resolve overlaps: nudge PEs that are too close together
            positioned.sort((a, b) => a.x - b.x);
            const minGap = 160;
            for (let i = 1; i < positioned.length; i++) {
                const gap = positioned[i].x - positioned[i - 1].x;
                if (gap < minGap) {
                    positioned[i].x = positioned[i - 1].x + minGap;
                }
            }
            
            // Place unconnected PEs evenly across remaining space
            if (unconnected.length > 0) {
                layoutTierSymmetric(unconnected, currentY, 'PE (unconnected)');
            }
            
            console.log(`[DNAAS Layout] PE: ${positioned.length} aligned under LEAFs, ${unconnected.length} unconnected`);
            currentY += tierSpacing;
        }
        
        if (categories.other.length > 0) { layoutTierSymmetric(categories.other, currentY, 'Other'); }
        
        console.log(`[DNAAS Layout] ✓ Symmetrical layout complete`);
        if (editor.debugger) {
            editor.debugger.logSuccess(`🌳 Symmetric Layout: ${devices.length} devices in ${Object.values(tierCounts).filter(c => c > 0).length} tiers`);
        }
    },

    /**
     * Load DNAAS discovery data
     * Extracted from topology.js for modular architecture
     */
    loadDnaasData(editor, data) {
        if (!data || !data.objects) {
            editor.showToast('Invalid discovery data', 'error');
            return;
        }
        
        if (data.metadata) {
            window._dnaasDiscoveryData = data;
            console.log('[DNAAS] Discovery data cached:', data.metadata?.bridge_domains?.length || 0, 'BDs');
        }
        
        const doLoad = () => {
            editor.saveState();
            editor.objects = data.objects || [];
            
            editor.applyDnaasHierarchicalLayout(editor.objects);
            
            editor.objects.forEach((obj, index) => {
                if (obj.type === 'device') {
                    if (obj.x === undefined || obj.y === undefined || isNaN(obj.x) || isNaN(obj.y)) {
                        obj.x = 200 + (index % 5) * 150;
                        obj.y = 200 + Math.floor(index / 5) * 150;
                    }
                    if (!obj.radius) obj.radius = 50;
                    
                    if (obj.sshConfig) {
                        obj.sshConfig = {
                            host: obj.sshConfig.host || obj.sshConfig.hostBackup || '',
                            hostBackup: obj.sshConfig.hostBackup || '',
                            user: obj.sshConfig.user || 'dnroot',
                            password: obj.sshConfig.password || 'dnroot'
                        };
                    }
                }
            });
            
            const deviceIds = editor.objects.filter(o => o.type === 'device').map(o => parseInt(o.id.replace(/\D/g, '')) || 0);
            const linkIds = editor.objects.filter(o => o.type === 'link' || o.type === 'unbound').map(o => parseInt(o.id.replace(/\D/g, '')) || 0);
            const textIds = editor.objects.filter(o => o.type === 'text').map(o => parseInt(o.id.replace(/\D/g, '')) || 0);
            editor.deviceIdCounter = deviceIds.length > 0 ? Math.max(...deviceIds) + 1 : 0;
            editor.linkIdCounter = linkIds.length > 0 ? Math.max(...linkIds) + 1 : 0;
            editor.textIdCounter = textIds.length > 0 ? Math.max(...textIds) + 1 : 0;
            
            editor.selectedObject = null;
            editor.selectedObjects = [];
            
            const devices = editor.objects.filter(o => o.type === 'device');
            if (devices.length > 0) {
                const labelBuffer = 100;
                let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
                
                devices.forEach(device => {
                    const radius = device.radius || 50;
                    minX = Math.min(minX, device.x - radius - labelBuffer);
                    maxX = Math.max(maxX, device.x + radius + labelBuffer);
                    minY = Math.min(minY, device.y - radius - 30);
                    maxY = Math.max(maxY, device.y + radius + 50);
                });
                
                const topologyWidth = maxX - minX;
                const topologyHeight = maxY - minY;
                const padding = 80;
                
                const cw = editor.canvasW || editor.canvas.width;
                const ch = editor.canvasH || editor.canvas.height;
                const availableWidth = cw - padding * 2;
                const availableHeight = ch - padding * 2;
                
                const zoomX = availableWidth / topologyWidth;
                const zoomY = availableHeight / topologyHeight;
                
                editor.zoom = Math.min(1.0, Math.min(zoomX, zoomY));
                editor.zoom = Math.max(0.4, editor.zoom);
                
                const centerX = (minX + maxX) / 2;
                const centerY = (minY + maxY) / 2;
                editor.panOffset = {
                    x: (cw / 2) - centerX * editor.zoom,
                    y: (ch / 2) - centerY * editor.zoom
                };
            } else {
                editor.zoom = 1;
                editor.panOffset = { x: 0, y: 0 };
            }
            
            editor.draw();
            
            if (data.metadata && data.metadata.bridge_domains && data.metadata.bridge_domains.length > 0) {
                editor._multiBDMetadata = data.metadata;
                editor.showBDLegend(data.metadata.bridge_domains);
                editor.updateBDHierarchyButton();
            } else {
                editor.updateBDHierarchyButton();
            }
            
            if (editor.debugger) {
                editor.debugger.logSuccess(`DNAAS discovery loaded: ${editor.objects.length} objects`);
            }
        };
        
        if (editor.objects.length > 0) {
            editor.showConfirmDialog(
                'Replace Current Canvas?',
                `This will replace the current canvas (${editor.objects.length} objects) with the discovered topology. Continue?`,
                doLoad
            );
        } else {
            doLoad();
        }
    }
};

console.log('[topology-dnaas-operations.js] DnaasOperations module loaded');
