/**
 * topology-curve-mode.js - Link Curve Mode Management
 * 
 * Extracted from topology.js for modular architecture.
 * Contains curve mode switching, UI updates, and curve calculations.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.CurveModeManager = {

    /**
     * Set global curve mode: 'auto' (magnetic repulsion), 'manual' (user-draggable)
     */
    setGlobalMode(editor, mode) {
        if (!['auto', 'manual'].includes(mode)) return;
        
        const oldMode = editor.globalCurveMode;
        const allLinks = editor.objects.filter(o => o.type === 'link' || o.type === 'unbound');
        
        // SEAMLESS transitions for all links using global mode
        for (const link of allLinks) {
            if (link.curveMode) continue;
            
            // AUTO → MANUAL: Ensure manualCurvePoint exists
            if (oldMode === 'auto' && mode === 'manual') {
                if (link.manualCurvePoint) {
                    if (editor.debugger) {
                        editor.debugger.logInfo(`→Manual: Kept existing curve for ${link.id}`);
                    }
                    continue;
                }
                
                // Try to restore from keepCurve data
                if (link.keepCurve && link.savedCurveOffset && link._renderedEndpoints) {
                    const midX = (link._renderedEndpoints.startX + link._renderedEndpoints.endX) / 2;
                    const midY = (link._renderedEndpoints.startY + link._renderedEndpoints.endY) / 2;
                    const linkLength = Math.sqrt(
                        Math.pow(link._renderedEndpoints.endX - link._renderedEndpoints.startX, 2) + 
                        Math.pow(link._renderedEndpoints.endY - link._renderedEndpoints.startY, 2)
                    ) || 1;
                    const cpX = midX + link.savedCurveOffset.cp1OffsetX * linkLength;
                    const cpY = midY + link.savedCurveOffset.cp1OffsetY * linkLength;
                    const visualMidX = 0.125 * link._renderedEndpoints.startX + 0.75 * cpX + 0.125 * link._renderedEndpoints.endX;
                    const visualMidY = 0.125 * link._renderedEndpoints.startY + 0.75 * cpY + 0.125 * link._renderedEndpoints.endY;
                    link.manualCurvePoint = { x: visualMidX, y: visualMidY };
                    if (editor.debugger) {
                        editor.debugger.logInfo(`KeepCurve→Manual: Restored curve for ${link.id}`);
                    }
                    continue;
                }
                
                // Capture from auto curve
                const autoCurvePoint = this.getAutoCurveMidpoint(editor, link);
                if (autoCurvePoint) {
                    link.manualCurvePoint = { x: autoCurvePoint.x, y: autoCurvePoint.y };
                    if (editor.debugger) {
                        editor.debugger.logInfo(`Auto→Manual: Captured curve for ${link.id}`);
                    }
                }
            }
            // MANUAL → AUTO: Clear keepCurve so auto mode works naturally
            else if (oldMode === 'manual' && mode === 'auto') {
                delete link.keepCurve;
                delete link.savedCurveOffset;
                
                if (editor.debugger) {
                    editor.debugger.logInfo(`→Auto: Cleared keepCurve for ${link.id} (manualCurvePoint preserved)`);
                }
            }
        }
        
        editor.globalCurveMode = mode;
        
        // Clear any hover/drag state
        editor.hoveredLinkMidpoint = null;
        editor.draggingCurveHandle = null;
        editor._potentialCPDrag = null;
        editor.dragging = false;
        editor.stretchingLink = null;
        
        this.updateUI(editor);
        editor.draw();
        editor.scheduleAutoSave();
    },

    /**
     * Update UI to reflect current global curve mode
     */
    updateUI(editor) {
        const autoBtn = document.getElementById('btn-curve-auto');
        const manualBtn = document.getElementById('btn-curve-manual');
        
        if (autoBtn) {
            if (editor.globalCurveMode === 'auto') {
                autoBtn.classList.add('active');
            } else {
                autoBtn.classList.remove('active');
            }
        }
        
        if (manualBtn) {
            if (editor.globalCurveMode === 'manual') {
                manualBtn.classList.add('active');
            } else {
                manualBtn.classList.remove('active');
            }
        }
        
        const curveMagnitudeControl = document.getElementById('curve-magnitude-control');
        if (curveMagnitudeControl) {
            curveMagnitudeControl.style.display = editor.globalCurveMode === 'auto' ? 'block' : 'none';
        }
        
        const curveModeButtons = document.getElementById('curve-mode-buttons');
        if (curveModeButtons) {
            curveModeButtons.style.display = editor.linkCurveMode ? 'flex' : 'none';
        }
    },

    /**
     * Get effective curve mode for a link (per-link override or global)
     */
    getEffectiveMode(editor, link) {
        if (link.curveMode) {
            return link.curveMode;
        }
        
        if (!editor.linkCurveMode) {
            return 'off';
        }
        
        return editor.globalCurveMode;
    },

    /**
     * Get the current endpoints of a link
     */
    getEndpoints(editor, link) {
        let startX, startY, endX, endY;
        
        if (link.type === 'unbound') {
            const dev1 = link.device1 ? editor.objects.find(o => o.id === link.device1) : null;
            const dev2 = link.device2 ? editor.objects.find(o => o.id === link.device2) : null;
            
            startX = dev1 ? dev1.x : link.start.x;
            startY = dev1 ? dev1.y : link.start.y;
            endX = dev2 ? dev2.x : link.end.x;
            endY = dev2 ? dev2.y : link.end.y;
        } else if (link.type === 'link') {
            const dev1 = editor.objects.find(o => o.id === link.device1);
            const dev2 = editor.objects.find(o => o.id === link.device2);
            if (!dev1 || !dev2) return null;
            startX = dev1.x;
            startY = dev1.y;
            endX = dev2.x;
            endY = dev2.y;
        } else {
            return null;
        }
        
        return { startX, startY, endX, endY };
    },

    /**
     * Get the visual midpoint ON the curve (at t=0.5)
     */
    getMidpoint(editor, link, overrideEndpoints = null) {
        let startX, startY, endX, endY;
        
        if (overrideEndpoints) {
            startX = overrideEndpoints.startX;
            startY = overrideEndpoints.startY;
            endX = overrideEndpoints.endX;
            endY = overrideEndpoints.endY;
        } else if (link.type === 'unbound' && link._renderedEndpoints) {
            startX = link._renderedEndpoints.startX;
            startY = link._renderedEndpoints.startY;
            endX = link._renderedEndpoints.endX;
            endY = link._renderedEndpoints.endY;
        } else if (link.type === 'unbound' && link.start && link.end) {
            startX = link.start.x;
            startY = link.start.y;
            endX = link.end.x;
            endY = link.end.y;
        } else if (link._renderedEndpoints) {
            startX = link._renderedEndpoints.startX;
            startY = link._renderedEndpoints.startY;
            endX = link._renderedEndpoints.endX;
            endY = link._renderedEndpoints.endY;
        } else {
            const renderedEndpoints = editor.getLinkRenderedEndpoints(link);
            if (!renderedEndpoints) return null;
            startX = renderedEndpoints.startX;
            startY = renderedEndpoints.startY;
            endX = renderedEndpoints.endX;
            endY = renderedEndpoints.endY;
        }
        
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;
        
        if (link.manualControlPoint) {
            return { x: link.manualControlPoint.x, y: link.manualControlPoint.y };
        }
        
        if (link.manualCurvePoint) {
            return { x: link.manualCurvePoint.x, y: link.manualCurvePoint.y };
        }
        
        const attachedText = editor.getAttachedTextAsCP(link);
        if (attachedText) {
            return { x: attachedText.x, y: attachedText.y };
        }
        
        if (link.manualCurveOffset) {
            const straightMidX = (startX + endX) / 2;
            const straightMidY = (startY + endY) / 2;
            
            const bezierCP = editor.getManualCurveBezierControlPoint(link, { startX, startY, endX, endY });
            if (bezierCP) {
                const targetMidX = (bezierCP.x * 3 + straightMidX) / 4;
                const targetMidY = (bezierCP.y * 3 + straightMidY) / 4;
                return { x: targetMidX, y: targetMidY };
            }
            return { x: straightMidX, y: straightMidY };
        }
        
        if (editor.linkCurveMode && link._cp1 && link._cp2 && link._renderedEndpoints) {
            const visualMidX = 0.125 * startX + 0.375 * link._cp1.x + 0.375 * link._cp2.x + 0.125 * endX;
            const visualMidY = 0.125 * startY + 0.375 * link._cp1.y + 0.375 * link._cp2.y + 0.125 * endY;
            return { x: visualMidX, y: visualMidY };
        }
        
        return { x: midX, y: midY };
    },

    /**
     * Get the current AUTO curve's visual midpoint position
     */
    getAutoCurveMidpoint(editor, link) {
        if (!link) return null;
        
        if (link._cp1 && link._cp2 && link._renderedEndpoints) {
            const startX = link._renderedEndpoints.startX;
            const startY = link._renderedEndpoints.startY;
            const endX = link._renderedEndpoints.endX;
            const endY = link._renderedEndpoints.endY;
            
            const visualMidX = 0.125 * startX + 0.375 * link._cp1.x + 0.375 * link._cp2.x + 0.125 * endX;
            const visualMidY = 0.125 * startY + 0.375 * link._cp1.y + 0.375 * link._cp2.y + 0.125 * endY;
            
            return { x: visualMidX, y: visualMidY };
        }
        
        let startX, startY, endX, endY;
        
        if (link.type === 'unbound') {
            if (link._renderedEndpoints) {
                startX = link._renderedEndpoints.startX;
                startY = link._renderedEndpoints.startY;
                endX = link._renderedEndpoints.endX;
                endY = link._renderedEndpoints.endY;
            } else if (link.start && link.end) {
                startX = link.start.x;
                startY = link.start.y;
                endX = link.end.x;
                endY = link.end.y;
            } else {
                return null;
            }
        } else if (link.type === 'link') {
            if (link._renderedEndpoints) {
                startX = link._renderedEndpoints.startX;
                startY = link._renderedEndpoints.startY;
                endX = link._renderedEndpoints.endX;
                endY = link._renderedEndpoints.endY;
            } else {
                const dev1 = editor.objects.find(o => o.id === link.device1);
                const dev2 = editor.objects.find(o => o.id === link.device2);
                if (!dev1 || !dev2) return null;
                startX = dev1.x;
                startY = dev1.y;
                endX = dev2.x;
                endY = dev2.y;
            }
        } else {
            return null;
        }
        
        const straightMidX = (startX + endX) / 2;
        const straightMidY = (startY + endY) / 2;
        
        return { x: straightMidX, y: straightMidY };
    }
};

console.log('[topology-curve-mode.js] CurveModeManager loaded');
