// ============================================================================
// TOPOLOGY LINK MANAGER MODULE
// ============================================================================
// Handles link creation, BUL chain management, merging/unmerging, styling.
// This is a wrapper module that delegates to editor methods.
//
// BUL TERMINOLOGY:
//   UL (Unbound Link): Single link with 0-2 device attachments
//   BUL (Bound Unbound Link): Multiple ULs merged into a chain
//   TP (Terminal Point): FREE endpoint - not attached to device, not connected to another link
//   MP (Merge Point): Where two ULs connect in a BUL chain
//   HEAD: First link in BUL chain (parent of all)
//   TAIL: Last link in BUL chain
//
// Usage:
//   const linkMgr = new LinkManager(editor);
//   linkMgr.getAll();
//   linkMgr.analyzeBULChain(link);
// ============================================================================

class LinkManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========================================================================
    // ACCESSOR - Get objects from editor
    // ========================================================================
    
    get objects() { return this.editor.objects || []; }

    // ========== FINDING ==========
    
    /**
     * Find link at world coordinates
     * @param {number} x - World X
     * @param {number} y - World Y
     * @returns {object|null} Link object or null
     */
    findAt(x, y) {
        if (this.editor.findLinkAt) {
            return this.editor.findLinkAt(x, y);
        }
        return null;
    }

    /**
     * Find nearest link to a point
     * @param {number} x - World X
     * @param {number} y - World Y
     * @param {number} maxDistance - Maximum search distance
     * @returns {object|null} Nearest link or null
     */
    findNearestToPoint(x, y, maxDistance = 50) {
        if (this.editor.findNearestLinkToPoint) {
            return this.editor.findNearestLinkToPoint(x, y, maxDistance);
        }
        return null;
    }

    /**
     * Get all links
     * @returns {array} Array of link objects
     */
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'link') || [];
    }

    /**
     * Get selected links
     * @returns {array} Array of selected links
     */
    getSelected() {
        return this.editor.selectedObjects?.filter(obj => obj.type === 'link') || [];
    }

    /**
     * Get link by ID
     * @param {string} id - Link ID
     * @returns {object|null} Link or null
     */
    getById(id) {
        return this.getAll().find(l => l.id === id) || null;
    }

    // ========== BUL CHAIN ANALYSIS (MIGRATED) ==========
    
    /**
     * Get all links merged with a link (entire BUL chain)
     * MIGRATED from topology.js getAllMergedLinks()
     * @param {object} link - Any link in the chain
     * @returns {array} All links in the chain
     */
    getAllMerged(link) {
        if (!link) return [];
        
        const mergedSet = new Set();
        const toProcess = [link];
        const processed = new Set();
        
        while (toProcess.length > 0) {
            const currentLink = toProcess.pop();
            
            // Skip if already processed
            if (processed.has(currentLink.id)) continue;
            processed.add(currentLink.id);
            
            // Add to result set
            mergedSet.add(currentLink);
            
            // Check for merged partner (parent -> child)
            if (currentLink.mergedWith) {
                const childLink = this.objects.find(o => o.id === currentLink.mergedWith.linkId);
                if (childLink && !processed.has(childLink.id)) {
                    toProcess.push(childLink);
                }
            }
            
            // Check for merged parent (if this is a child)
            if (currentLink.mergedInto) {
                const parentLink = this.objects.find(o => o.id === currentLink.mergedInto.parentId);
                if (parentLink && !processed.has(parentLink.id)) {
                    toProcess.push(parentLink);
                }
            }
            
            // Also check if any OTHER links are merged with this one
            this.objects.forEach(obj => {
                if (obj.type === 'unbound' && !processed.has(obj.id)) {
                    if (obj.mergedWith && obj.mergedWith.linkId === currentLink.id) {
                        toProcess.push(obj);
                    } else if (obj.mergedInto && obj.mergedInto.parentId === currentLink.id) {
                        toProcess.push(obj);
                    }
                }
            });
        }
        
        return Array.from(mergedSet);
    }

    /**
     * Check if an endpoint is connected to another link (MP)
     * MIGRATED from topology.js isEndpointConnected()
     * @param {object} link - Link to check
     * @param {string} endpoint - 'start' or 'end'
     * @returns {boolean} True if connected to another link
     */
    isEndpointConnected(link, endpoint) {
        if (!link) return false;
        
        // Check if connected to child
        if (this._isEndpointConnectedToChild(link, endpoint)) return true;
        
        // Check if connected to parent
        if (this._isEndpointConnectedToParent(link, endpoint)) return true;
        
        return false;
    }
    
    _getParentConnectionEndpoint(link) {
        if (!link?.mergedWith) return null;
        if (link.mergedWith.connectionEndpoint) return link.mergedWith.connectionEndpoint;
        return link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
    }
    
    _getChildConnectionEndpoint(link) {
        if (!link?.mergedInto) return null;
        if (link.mergedInto.childEndpoint) return link.mergedInto.childEndpoint;
        const parentLink = this.objects.find(o => o.id === link.mergedInto.parentId);
        if (parentLink?.mergedWith) {
            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
            return childFreeEnd === 'start' ? 'end' : 'start';
        }
        return null;
    }
    
    _isEndpointConnectedToChild(link, endpoint) {
        const connection = this._getParentConnectionEndpoint(link);
        return connection ? connection === endpoint : false;
    }
    
    _isEndpointConnectedToParent(link, endpoint) {
        const connection = this._getChildConnectionEndpoint(link);
        return connection ? connection === endpoint : false;
    }

    /**
     * Analyze BUL chain structure - count TPs and MPs
     * MIGRATED from topology.js analyzeBULChain()
     * @param {object} link - Any link in the chain
     * @returns {object} Chain analysis {linkCount, tpCount, mpCount, links, isValid}
     */
    analyzeBULChain(link) {
        const allLinks = this.getAllMerged(link);
        let tpCount = 0;
        let mpCount = 0;
        
        // Count MPs (merge points) - each mergedWith relationship creates one MP
        allLinks.forEach(chainLink => {
            if (chainLink.mergedWith) {
                mpCount++;
            }
        });
        
        // Count actual free TPs by checking BOTH mergedWith AND mergedInto
        allLinks.forEach(chainLink => {
            // Check start endpoint
            let startIsConnected = false;
            
            if (chainLink.mergedWith) {
                if (chainLink.mergedWith.parentFreeEnd === 'end') {
                    startIsConnected = true;
                }
            }
            if (chainLink.mergedInto) {
                const parentLink = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    if (parentLink.mergedWith.childFreeEnd === 'end') {
                        startIsConnected = true;
                    }
                }
            }
            if (!startIsConnected) tpCount++;
            
            // Check end endpoint
            let endIsConnected = false;
            
            if (chainLink.mergedWith) {
                if (chainLink.mergedWith.parentFreeEnd === 'start') {
                    endIsConnected = true;
                }
            }
            if (chainLink.mergedInto) {
                const parentLink = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
                if (parentLink && parentLink.mergedWith) {
                    if (parentLink.mergedWith.childFreeEnd === 'start') {
                        endIsConnected = true;
                    }
                }
            }
            if (!endIsConnected) tpCount++;
        });
        
        return {
            linkCount: allLinks.length,
            tpCount,
            mpCount,
            links: allLinks,
            isValid: (tpCount === 2 && mpCount === allLinks.length - 1)
        };
    }

    /**
     * Get ALL devices connected to TPs across the entire BUL chain
     * MIGRATED from topology.js getAllConnectedDevices()
     * @param {object} link - Any link in chain
     * @returns {object} {deviceIds, devices, count, links}
     */
    getAllConnectedDevices(link) {
        const deviceIds = new Set();
        const deviceObjects = [];
        
        const allMergedLinks = this.getAllMerged(link);
        
        for (const chainLink of allMergedLinks) {
            if (chainLink.device1 && !deviceIds.has(chainLink.device1)) {
                deviceIds.add(chainLink.device1);
                const device = this.objects.find(obj => obj.id === chainLink.device1);
                if (device) deviceObjects.push(device);
            }
            
            if (chainLink.device2 && !deviceIds.has(chainLink.device2)) {
                deviceIds.add(chainLink.device2);
                const device = this.objects.find(obj => obj.id === chainLink.device2);
                if (device) deviceObjects.push(device);
            }
        }
        
        return {
            deviceIds: Array.from(deviceIds),
            devices: deviceObjects,
            count: deviceIds.size,
            links: allMergedLinks
        };
    }

    /**
     * Get the two endpoint devices from a BUL chain
     * MIGRATED from topology.js getBULEndpointDevices()
     * @param {object} link - Any link in chain
     * @returns {object} {device1, device2, hasEndpoints}
     */
    getBULEndpoints(link) {
        // Simple UL with both devices attached
        if (link.device1 && link.device2) {
            const [dev1, dev2] = [link.device1, link.device2].sort();
            return { device1: dev1, device2: dev2, hasEndpoints: true };
        }
        
        // Check the BUL chain for endpoint devices
        const connectedInfo = this.getAllConnectedDevices(link);
        
        if (connectedInfo.count === 2) {
            const [dev1, dev2] = connectedInfo.deviceIds.sort();
            return { device1: dev1, device2: dev2, hasEndpoints: true };
        }
        
        if (connectedInfo.count === 1) {
            return { device1: connectedInfo.deviceIds[0], device2: null, hasEndpoints: false };
        }
        
        return { device1: null, device2: null, hasEndpoints: false };
    }

    /**
     * Check if two links already share a merge point
     * @param {object} link1 - First link
     * @param {object} link2 - Second link
     * @returns {boolean} True if already merged
     */
    alreadyShareMP(link1, link2) {
        if (!link1 || !link2) return false;
        
        // Check if link1 is parent of link2
        if (link1.mergedWith && link1.mergedWith.linkId === link2.id) return true;
        
        // Check if link2 is parent of link1
        if (link2.mergedWith && link2.mergedWith.linkId === link1.id) return true;
        
        // Check via mergedInto
        if (link1.mergedInto && link1.mergedInto.parentId === link2.id) return true;
        if (link2.mergedInto && link2.mergedInto.parentId === link1.id) return true;
        
        return false;
    }

    /**
     * Check if link is HEAD of BUL chain
     * @param {object} link - Link to check
     * @returns {boolean} True if HEAD
     */
    isHead(link) {
        return !link.parentLink;
    }

    /**
     * Check if link is TAIL of BUL chain
     * @param {object} link - Link to check
     * @returns {boolean} True if TAIL
     */
    isTail(link) {
        return !link.mergedWith;
    }

    /**
     * Check if link is in the MIDDLE of BUL chain
     * @param {object} link - Link to check
     * @returns {boolean} True if MIDDLE
     */
    isMiddle(link) {
        return link.parentLink && link.mergedWith;
    }

    /**
     * Get HEAD of BUL chain
     * @param {object} link - Any link in chain
     * @returns {object} HEAD link
     */
    getHead(link) {
        let current = link;
        while (current.parentLink) {
            const parent = this.getById(current.parentLink);
            if (!parent) break;
            current = parent;
        }
        return current;
    }

    /**
     * Get TAIL of BUL chain
     * @param {object} link - Any link in chain
     * @returns {object} TAIL link
     */
    getTail(link) {
        let current = link;
        while (current.mergedWith) {
            const child = this.getById(current.mergedWith);
            if (!child) break;
            current = child;
        }
        return current;
    }

    // ========== ENDPOINTS ==========
    
    /**
     * Get link endpoints (world coordinates)
     * @param {object} link - Link object
     * @returns {object} {start: {x,y}, end: {x,y}}
     */
    getEndpoints(link) {
        if (this.editor.getLinkEndpoints) {
            return this.editor.getLinkEndpoints(link);
        }
        return { start: link.startPoint, end: link.endPoint };
    }

    /**
     * Get link rendered endpoints (accounting for curves)
     * @param {object} link - Link object
     * @returns {object} Rendered endpoints
     */
    getRenderedEndpoints(link) {
        if (this.editor.getLinkRenderedEndpoints) {
            return this.editor.getLinkRenderedEndpoints(link);
        }
        return this.getEndpoints(link);
    }

    /**
     * Get link midpoint
     * @param {object} link - Link object
     * @returns {object} {x, y}
     */
    getMidpoint(link) {
        if (this.editor.getLinkMidpoint) {
            return this.editor.getLinkMidpoint(link);
        }
        const eps = this.getEndpoints(link);
        return {
            x: (eps.start.x + eps.end.x) / 2,
            y: (eps.start.y + eps.end.y) / 2
        };
    }

    /**
     * Get link endpoint near a point
     * @param {object} link - Link object
     * @param {object} point - {x, y}
     * @param {number} tolerance - Distance tolerance
     * @returns {string|null} 'start', 'end', or null
     */
    getEndpointNearPoint(link, point, tolerance = 0.75) {
        if (this.editor.getLinkEndpointNearPoint) {
            return this.editor.getLinkEndpointNearPoint(link, point, tolerance);
        }
        return null;
    }

    // ========== ATTACHMENT INFO ==========
    
    /**
     * Get link attachment info (devices, interfaces)
     * @param {object} link - Link object
     * @returns {object} Attachment info
     */
    getAttachmentInfo(link) {
        if (this.editor.getLinkAttachmentInfo) {
            return this.editor.getLinkAttachmentInfo(link);
        }
        return {};
    }

    /**
     * Get all devices connected to a link
     * @param {object} link - Link object
     * @returns {array} Connected devices
     */
    getConnectedDevices(link) {
        if (this.editor.getAllConnectedDevices) {
            return this.editor.getAllConnectedDevices(link);
        }
        return [];
    }

    // ========== STYLING ==========
    
    /**
     * Set link style
     * @param {string} style - Style name
     */
    setStyle(style) {
        if (this.editor.setLinkStyle) {
            this.editor.setLinkStyle(style);
        }
    }

    /**
     * Cycle link style variants
     * @param {string} baseStyle - Base style name
     */
    cycleStyle(baseStyle) {
        if (this.editor.cycleLinkStyle) {
            this.editor.cycleLinkStyle(baseStyle);
        }
    }

    /**
     * Get link style variants
     * @param {string} baseStyle - Base style
     * @returns {array} Style variants
     */
    getStyleVariants(baseStyle) {
        if (this.editor.getLinkStyleVariants) {
            return this.editor.getLinkStyleVariants(baseStyle);
        }
        return [];
    }

    /**
     * Get max link width
     * @param {object} link - Link object
     * @returns {number} Max width
     */
    getMaxWidth(link) {
        if (this.editor.getMaxLinkWidth) {
            return this.editor.getMaxLinkWidth(link);
        }
        return link.width || 2;
    }

    // ========== CURVE OPERATIONS ==========
    
    /**
     * Toggle link curve mode
     */
    toggleCurveMode() {
        if (this.editor.toggleLinkCurveMode) {
            this.editor.toggleLinkCurveMode();
        }
    }

    /**
     * Check if point is near link body
     * @param {number} x - World X
     * @param {number} y - World Y
     * @param {object} link - Link object
     * @param {number} threshold - Distance threshold
     * @returns {boolean} True if near
     */
    isPointNearBody(x, y, link, threshold = 10) {
        if (this.editor.isPointNearLinkBody) {
            return this.editor.isPointNearLinkBody(x, y, link, threshold);
        }
        return false;
    }

    /**
     * Get closest point on curved link
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {object} link - Link object
     * @returns {object} {x, y, t}
     */
    getClosestPointOnCurve(px, py, link) {
        if (this.editor.getClosestPointOnCurvedLink) {
            const eps = this.getEndpoints(link);
            return this.editor.getClosestPointOnCurvedLink(px, py, link, eps.start, eps.end);
        }
        return null;
    }

    // ========== MODES ==========
    
    /**
     * Toggle continuous link mode
     */
    toggleContinuousMode() {
        if (this.editor.toggleLinkContinuousMode) {
            this.editor.toggleLinkContinuousMode();
        }
    }

    /**
     * Toggle sticky link mode
     */
    toggleStickyMode() {
        if (this.editor.toggleLinkStickyMode) {
            this.editor.toggleLinkStickyMode();
        }
    }

    /**
     * Toggle UL (Unbound Link) mode
     */
    toggleULMode() {
        if (this.editor.toggleLinkULMode) {
            this.editor.toggleLinkULMode();
        }
    }

    // ========== TOOLBAR ==========
    
    /**
     * Show link selection toolbar
     * @param {object} link - Selected link
     * @param {object} clickPos - Click position
     */
    showToolbar(link, clickPos = null) {
        if (this.editor.showLinkSelectionToolbar) {
            this.editor.showLinkSelectionToolbar(link, clickPos);
        }
    }

    /**
     * Hide link selection toolbar
     */
    hideToolbar() {
        if (this.editor.hideLinkSelectionToolbar) {
            this.editor.hideLinkSelectionToolbar();
        }
    }

    // ========== EDITOR ==========
    
    /**
     * Show link editor panel
     * @param {object} link - Link to edit
     */
    showEditor(link) {
        if (this.editor.showLinkEditor) {
            this.editor.showLinkEditor(link);
        }
    }

    /**
     * Hide link editor panel
     */
    hideEditor() {
        if (this.editor.hideLinkEditor) {
            this.editor.hideLinkEditor();
        }
    }

    /**
     * Show link details panel
     * @param {object} link - Link object
     */
    showDetails(link) {
        if (this.editor.showLinkDetails) {
            this.editor.showLinkDetails(link);
        }
    }

    /**
     * Hide link details panel
     */
    hideDetails() {
        if (this.editor.hideLinkDetails) {
            this.editor.hideLinkDetails();
        }
    }

    /**
     * Save link details
     */
    saveDetails() {
        if (this.editor.saveLinkDetails) {
            this.editor.saveLinkDetails();
        }
    }

    // ========== INTERFACE MENU ==========
    
    /**
     * Show link interface menu
     * @param {object} link - Link object
     */
    showInterfaceMenu(link) {
        if (this.editor.showLinkInterfaceMenu) {
            this.editor.showLinkInterfaceMenu(link);
        }
    }

    // ========== DUPLICATION ==========
    
    /**
     * Duplicate entire BUL chain
     * @param {object} sourceLink - Source link (any in chain)
     * @param {number} offsetX - X offset
     * @param {number} offsetY - Y offset
     * @returns {object|null} New chain head
     */
    duplicateBULChain(sourceLink, offsetX, offsetY) {
        if (this.editor.duplicateBULChain) {
            return this.editor.duplicateBULChain(sourceLink, offsetX, offsetY);
        }
        return null;
    }

    // ========== INDEX CALCULATION ==========
    
    /**
     * Calculate link index (for parallel links)
     * @param {object} link - Link object
     * @returns {number} Link index
     */
    calculateIndex(link) {
        if (this.editor.calculateLinkIndex) {
            return this.editor.calculateLinkIndex(link);
        }
        return 0;
    }

    // ========== TEXT BOXES ==========
    
    /**
     * Create link text boxes
     */
    createTextBoxes() {
        if (this.editor.createLinkTextBoxes) {
            this.editor.createLinkTextBoxes();
        }
    }

    // ========== UTILITY ==========
    
    /**
     * Get count of links
     * @returns {number} Count
     */
    getCount() {
        return this.getAll().length;
    }

    /**
     * Get count of BUL chains
     * @returns {number} Count of unique chains
     */
    getBULChainCount() {
        const links = this.getAll();
        const heads = links.filter(l => this.isHead(l));
        return heads.length;
    }

    /**
     * Delete a link (handles BUL chain cleanup)
     * @param {object} link - Link to delete
     */
    delete(link) {
        if (link && this.editor.handleULDeletionInBUL) {
            this.editor.handleULDeletionInBUL(link);
        } else if (link && this.editor.objects) {
            const idx = this.editor.objects.indexOf(link);
            if (idx !== -1) {
                this.editor.objects.splice(idx, 1);
                this.editor.draw();
                this.editor.saveState();
            }
        }
    }

    /**
     * Check if link has Terminal Points (free endpoints)
     * Uses the migrated isEndpointConnected() for accurate detection
     * @param {object} link - Link to check
     * @returns {object} {start: boolean, end: boolean}
     */
    hasTerminalPoints(link) {
        const startFree = !link.device1 && !this.isEndpointConnected(link, 'start');
        const endFree = !link.device2 && !this.isEndpointConnected(link, 'end');
        return { start: startFree, end: endFree };
    }

    /**
     * Get link chain position info
     * @param {object} link - Link to analyze
     * @returns {object} {isHead, isTail, isMiddle, chainLength}
     */
    getChainPosition(link) {
        const chain = this.getAllMerged(link);
        return {
            isHead: this.isHead(link),
            isTail: this.isTail(link),
            isMiddle: this.isMiddle(link),
            chainLength: chain.length
        };
    }
}

/**
 * Repair corrupted links - Fix links with endpoints stretched to wrong positions
 * Extracted from topology.js for modular architecture
 */
window.LinkUtils = {
    repairCorruptedLinks(editor) {
        console.log('[LinkRepair] Starting link repair...');
        let repairCount = 0;
        
        const devices = editor.objects.filter(o => o.type === 'device');
        if (devices.length === 0) {
            console.log('No devices found - cannot determine bounds');
            return 0;
        }
        
        // Calculate bounding box of all devices
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        devices.forEach(d => {
            minX = Math.min(minX, d.x);
            maxX = Math.max(maxX, d.x);
            minY = Math.min(minY, d.y);
            maxY = Math.max(maxY, d.y);
        });
        
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        const threshold = 1500; // If endpoint is more than 1500px from center, it's corrupted
        
        console.log('Device center:', centerX, centerY, 'threshold:', threshold);
        
        // Check each unbound link
        editor.objects.forEach(link => {
            if (link.type !== 'unbound') return;
            if (!link.start || !link.end) return;
            
            const startDist = Math.sqrt(Math.pow((link.start.x || 0) - centerX, 2) + Math.pow((link.start.y || 0) - centerY, 2));
            const endDist = Math.sqrt(Math.pow((link.end.x || 0) - centerX, 2) + Math.pow((link.end.y || 0) - centerY, 2));
            
            const startCorrupted = startDist > threshold || isNaN(link.start.x) || isNaN(link.start.y);
            const endCorrupted = endDist > threshold || isNaN(link.end.x) || isNaN(link.end.y);
            
            if (startCorrupted || endCorrupted) {
                console.log(`[LinkRepair] Repairing link ${link.id}: startDist=${startDist.toFixed(0)}, endDist=${endDist.toFixed(0)}`);
                
                const device1 = link.device1 ? editor.objects.find(o => o.id === link.device1) : null;
                const device2 = link.device2 ? editor.objects.find(o => o.id === link.device2) : null;
                
                // Repair start position
                if (startCorrupted) {
                    if (device1) {
                        const targetX = device2 ? device2.x : (device1.x + 150);
                        const targetY = device2 ? device2.y : device1.y;
                        const angle = Math.atan2(targetY - device1.y, targetX - device1.x);
                        const radius = device1.radius || 30;
                        link.start.x = device1.x + Math.cos(angle) * radius;
                        link.start.y = device1.y + Math.sin(angle) * radius;
                    } else {
                        link.start.x = centerX - 100;
                        link.start.y = centerY;
                    }
                }
                
                // Repair end position
                if (endCorrupted) {
                    if (device2) {
                        const targetX = device1 ? device1.x : (device2.x - 150);
                        const targetY = device1 ? device1.y : device2.y;
                        const angle = Math.atan2(targetY - device2.y, targetX - device2.x);
                        const radius = device2.radius || 30;
                        link.end.x = device2.x + Math.cos(angle) * radius;
                        link.end.y = device2.y + Math.sin(angle) * radius;
                    } else {
                        link.end.x = centerX + 100;
                        link.end.y = centerY;
                    }
                }
                
                // Reset curve points
                if (link.manualCurvePoint) {
                    link.manualCurvePoint.x = (link.start.x + link.end.x) / 2;
                    link.manualCurvePoint.y = (link.start.y + link.end.y) / 2;
                }
                if (link.manualControlPoint) {
                    link.manualControlPoint.x = (link.start.x + link.end.x) / 2;
                    link.manualControlPoint.y = (link.start.y + link.end.y) / 2;
                }
                
                // Fix connection points if part of a BUL chain
                if (link.mergedWith?.connectionPoint) {
                    const parentEnd = link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
                    link.mergedWith.connectionPoint.x = parentEnd === 'start' ? link.start.x : link.end.x;
                    link.mergedWith.connectionPoint.y = parentEnd === 'start' ? link.start.y : link.end.y;
                }
                if (link.mergedInto?.connectionPoint) {
                    const childEnd = link.mergedInto.childFreeEnd === 'start' ? 'end' : 'start';
                    link.mergedInto.connectionPoint.x = childEnd === 'start' ? link.start.x : link.end.x;
                    link.mergedInto.connectionPoint.y = childEnd === 'start' ? link.start.y : link.end.y;
                }
                
                repairCount++;
            }
        });
        
        // Also check Quick Links - shouldn't have x/y properties
        editor.objects.forEach(link => {
            if (link.type !== 'link') return;
            if (link.x !== undefined || link.y !== undefined) {
                console.log(`[LinkRepair] Cleaning Quick Link ${link.id}: removing corrupted x/y`);
                delete link.x;
                delete link.y;
                repairCount++;
            }
        });
        
        if (repairCount > 0) {
            console.log(`[OK] Repaired ${repairCount} corrupted links`);
            editor.updateAllConnectionPoints();
            editor.draw();
            if (typeof editor.saveTopology === 'function') {
                editor.saveTopology();
            } else if (window.FileOps && window.FileOps.quickSaveTopology) {
                window.FileOps.quickSaveTopology(editor);
            }
        } else {
            console.log('[OK] No corrupted links found');
        }
        
        return repairCount;
    }
};

// Export for module loading
window.LinkManager = LinkManager;
window.createLinkManager = function(editor) {
    return new LinkManager(editor);
};

console.log('[topology-links.js] LinkManager with BUL chain analysis loaded');
