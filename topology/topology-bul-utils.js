/**
 * topology-bul-utils.js - BUL (Bi-directional Unbound Link) Utility Functions
 * 
 * Extracted from topology.js for modular architecture.
 * Contains helper functions for working with merged/chained BULs.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.BulUtils = {

    /**
     * Calculate distance from a point to a line segment
     */
    distanceToLine(px, py, lineStart, lineEnd) {
        const A = px - lineStart.x;
        const B = py - lineStart.y;
        const C = lineEnd.x - lineStart.x;
        const D = lineEnd.y - lineStart.y;
        
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        
        if (lenSq !== 0) param = dot / lenSq;
        
        let xx, yy;
        if (param < 0) {
            xx = lineStart.x;
            yy = lineStart.y;
        } else if (param > 1) {
            xx = lineEnd.x;
            yy = lineEnd.y;
        } else {
            xx = lineStart.x + param * C;
            yy = lineStart.y + param * D;
        }
        
        const dx = px - xx;
        const dy = py - yy;
        return Math.sqrt(dx * dx + dy * dy);
    },

    /**
     * Check if two links already share an MP (connection point)
     */
    linksAlreadyShareMP(editor, link1, link2) {
        // Direct parent-child relationship
        if (link1.mergedWith && link1.mergedWith.linkId === link2.id) {
            return true;
        }
        if (link2.mergedWith && link2.mergedWith.linkId === link1.id) {
            return true;
        }
        if (link1.mergedInto && link1.mergedInto.parentId === link2.id) {
            return true;
        }
        if (link2.mergedInto && link2.mergedInto.parentId === link1.id) {
            return true;
        }
        
        // Check if they're both in the same merge chain
        const link1Chain = this.getAllMergedLinks(editor, link1);
        const link2Chain = this.getAllMergedLinks(editor, link2);
        
        for (const chainLink1 of link1Chain) {
            for (const chainLink2 of link2Chain) {
                if (chainLink1.id === chainLink2.id) {
                    return true;
                }
            }
        }
        
        return false;
    },

    /**
     * Recursively find ALL merged links in the chain
     */
    getAllMergedLinks(editor, link) {
        const mergedSet = new Set();
        const toProcess = [link];
        const processed = new Set();
        
        while (toProcess.length > 0) {
            const currentLink = toProcess.pop();
            
            if (processed.has(currentLink.id)) continue;
            processed.add(currentLink.id);
            
            mergedSet.add(currentLink);
            
            // Check for merged partner (parent)
            if (currentLink.mergedWith) {
                const childLink = editor.objects.find(o => o.id === currentLink.mergedWith.linkId);
                if (childLink && !processed.has(childLink.id)) {
                    toProcess.push(childLink);
                }
            }
            
            // Check for merged parent (if this is a child)
            if (currentLink.mergedInto) {
                const parentLink = editor.objects.find(o => o.id === currentLink.mergedInto.parentId);
                if (parentLink && !processed.has(parentLink.id)) {
                    toProcess.push(parentLink);
                }
            }
            
            // Also check if any OTHER links are merged with this one
            editor.objects.forEach(obj => {
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
    },

    /**
     * Get the endpoint where parent connects to its child
     */
    getParentConnectionEndpoint(link) {
        if (!link?.mergedWith) return null;
        if (link.mergedWith.connectionEndpoint) return link.mergedWith.connectionEndpoint;
        return link.mergedWith.parentFreeEnd === 'start' ? 'end' : 'start';
    },

    /**
     * Get the endpoint where child connects to its parent
     */
    getChildConnectionEndpoint(editor, link) {
        if (!link?.mergedInto) return null;
        if (link.mergedInto.childEndpoint) return link.mergedInto.childEndpoint;
        const parentLink = editor.objects.find(o => o.id === link.mergedInto.parentId);
        if (parentLink?.mergedWith) {
            const childFreeEnd = parentLink.mergedWith.childFreeEnd;
            return childFreeEnd === 'start' ? 'end' : 'start';
        }
        return null;
    },

    /**
     * Check if endpoint is connected to a child link
     */
    isEndpointConnectedToChild(link, endpoint) {
        const connection = this.getParentConnectionEndpoint(link);
        return connection ? connection === endpoint : false;
    },

    /**
     * Check if endpoint is connected to a parent link
     */
    isEndpointConnectedToParent(editor, link, endpoint) {
        const connection = this.getChildConnectionEndpoint(editor, link);
        return connection ? connection === endpoint : false;
    },

    /**
     * Check if endpoint is connected (to either parent or child)
     */
    isEndpointConnected(editor, link, endpoint) {
        if (!link) return false;
        if (this.isEndpointConnectedToChild(link, endpoint)) return true;
        if (this.isEndpointConnectedToParent(editor, link, endpoint)) return true;
        return false;
    },

    /**
     * Get the opposite endpoint
     */
    getOppositeEndpoint(endpoint) {
        if (endpoint === 'start') return 'end';
        if (endpoint === 'end') return 'start';
        return null;
    },

    /**
     * Get the link endpoint nearest to a point
     */
    getLinkEndpointNearPoint(link, point, tolerance = 0.75) {
        if (!link || !point || !link.start || !link.end) return null;
        const distStart = Math.hypot(link.start.x - point.x, link.start.y - point.y);
        const distEnd = Math.hypot(link.end.x - point.x, link.end.y - point.y);
        
        if (!isFinite(distStart) || !isFinite(distEnd)) return null;
        
        if (distStart <= tolerance && distStart <= distEnd) return 'start';
        if (distEnd <= tolerance && distEnd < distStart) return 'end';
        return null;
    }
};

console.log('[topology-bul-utils.js] BulUtils loaded');
