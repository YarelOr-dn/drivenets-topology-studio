/**
 * topology-minimap.js - Minimap Navigation Module
 * 
 * Extracted from topology.js for modular architecture.
 * Contains minimap setup, rendering, and navigation functions.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.MinimapModule = {

    /**
     * Setup the minimap with event handlers
     * @param {Object} editor - TopologyEditor instance
     */
    setup(editor) {
        const minimapContainer = document.getElementById('minimap-container');
        const minimapCanvas = document.getElementById('minimap-canvas');
        const toggleBtn = document.getElementById('btn-toggle-minimap');
        
        if (!minimapContainer || !minimapCanvas) {
            console.warn('Minimap elements not found, skipping setup');
            return;
        }
        
        editor.minimap = {
            container: minimapContainer,
            canvas: minimapCanvas,
            ctx: minimapCanvas.getContext('2d'),
            isDragging: false,
            visible: true,
            targetPan: null,
            animationId: null,
            lastMoveTime: 0,
            zoom: 1.0,
            panX: 0,
            panY: 0,
            isPanning: false
        };
        
        // Load saved visibility preference
        const savedMinimapVisible = localStorage.getItem('minimapVisible');
        if (savedMinimapVisible === 'false') {
            editor.minimap.visible = false;
            minimapContainer.style.display = 'none';
            if (toggleBtn) toggleBtn.classList.remove('minimap-on');
            
        }
        
        // Toggle button handler
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggle(editor);
            });
        }
        
        // Prevent context menu on minimap for right-click panning
        minimapCanvas.addEventListener('contextmenu', (e) => e.preventDefault());
        minimapContainer.addEventListener('contextmenu', (e) => e.preventDefault());

        // Mousedown on minimap
        minimapContainer.addEventListener('mousedown', (e) => {
            if (e.target !== minimapCanvas && e.target !== minimapContainer) return;
            e.preventDefault();

            if (e.button === 2 && (editor.minimap.zoom || 1) > 1) {
                // Right-click drag when zoomed in: pan the minimap view
                editor.minimap.isPanning = true;
                editor.minimap._panStartMX = e.clientX;
                editor.minimap._panStartMY = e.clientY;
                editor.minimap._panStartX = editor.minimap.panX;
                editor.minimap._panStartY = editor.minimap.panY;
            } else if (e.button === 0) {
                // Left-click: navigate main canvas
                editor.minimap.isDragging = true;
                editor.minimap.lastMoveTime = performance.now();
                // Freeze bounds for duration of drag to prevent jitter
                editor.minimap._dragBounds = this.getBounds(editor);
                if (editor.minimap.animationId) {
                    cancelAnimationFrame(editor.minimap.animationId);
                    editor.minimap.animationId = null;
                }
                this.navigateFromDrag(editor, e);
                this.startDragLoop(editor);
            }
        });

        const handleMouseMove = (e) => {
            if (!editor.minimap) return;
            if (editor.minimap.isPanning) {
                e.preventDefault();
                const bounds = this.getBounds(editor);
                if (bounds && bounds.scale > 0) {
                    const dx = e.clientX - editor.minimap._panStartMX;
                    const dy = e.clientY - editor.minimap._panStartMY;
                    editor.minimap.panX = editor.minimap._panStartX - dx * 1.5 / bounds.scale;
                    editor.minimap.panY = editor.minimap._panStartY - dy * 1.5 / bounds.scale;
                    if (window.MinimapRender) {
                        window.MinimapRender.invalidateCache();
                        window.MinimapRender.scheduleRender(editor);
                    }
                }
            } else if (editor.minimap.isDragging) {
                e.preventDefault();
                this.updateDragTarget(editor, e);
            }
        };

        const handleMouseUp = (e) => {
            if (!editor.minimap) return;
            if (editor.minimap.isPanning) {
                editor.minimap.isPanning = false;
            }
            if (editor.minimap.isDragging) {
                editor.minimap.isDragging = false;
                delete editor.minimap._dragBounds;
                this.stopDragLoop(editor);
                editor.savePanOffset();
            }
        };

        document.addEventListener('mousemove', handleMouseMove, { passive: false });
        document.addEventListener('mouseup', handleMouseUp);

        minimapContainer.addEventListener('mousemove', (e) => {
            if (editor.minimap.isPanning || editor.minimap.isDragging) {
                e.preventDefault();
                if (editor.minimap.isDragging) this.updateDragTarget(editor, e);
            }
        }, { passive: false });

        // Scroll wheel / trackpad on minimap — zoom towards cursor
        const self = this;
        minimapCanvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const oldZ = editor.minimap.zoom || 1;

            if (oldZ > 1 && !e.ctrlKey && Math.abs(e.deltaX) > Math.abs(e.deltaY) * 0.5) {
                const bounds = self.getBounds(editor);
                if (bounds && bounds.scale > 0) {
                    editor.minimap.panX += e.deltaX * 2 / bounds.scale;
                    editor.minimap.panY += e.deltaY * 2 / bounds.scale;
                }
            } else {
                const sensitivity = e.ctrlKey ? 0.04 : 0.008;
                const delta = -e.deltaY * sensitivity;
                const newZ = Math.max(1, Math.min(8, oldZ * (1 + delta)));

                if (newZ !== oldZ) {
                    const rect = minimapCanvas.getBoundingClientRect();
                    const mx = e.clientX - rect.left;
                    const my = e.clientY - rect.top;

                    const ratio = newZ / oldZ;
                    editor.minimap.panX = mx / (188 * oldZ) * (newZ - oldZ) + editor.minimap.panX * ratio;
                    editor.minimap.panY = my / (100 * oldZ) * (newZ - oldZ) + editor.minimap.panY * ratio;
                    editor.minimap.zoom = newZ;
                }
            }

            if (editor.minimap.zoom <= 1.02) {
                editor.minimap.zoom = 1;
                editor.minimap.panX = 0;
                editor.minimap.panY = 0;
                delete editor.minimap._cachedBase;
            }
            if (window.MinimapRender) window.MinimapRender.invalidateCache();
            editor.renderMinimap();
        }, { passive: false });

        // +/- / reset buttons — only affect minimap zoom, not main canvas
        const mmZoomIn = document.getElementById('minimap-zoom-in');
        const mmZoomOut = document.getElementById('minimap-zoom-out');
        const mmZoomReset = document.getElementById('minimap-zoom-reset');
        if (mmZoomIn) mmZoomIn.addEventListener('click', (e) => {
            e.stopPropagation();
            editor.minimap.zoom = Math.min(10, (editor.minimap.zoom || 1) * 1.4);
            if (window.MinimapRender) window.MinimapRender.invalidateCache();
            editor.renderMinimap();
        });
        if (mmZoomOut) mmZoomOut.addEventListener('click', (e) => {
            e.stopPropagation();
            let newZoom = Math.max(1, (editor.minimap.zoom || 1) / 1.4);
            if (newZoom <= 1.01) newZoom = 1;
            editor.minimap.zoom = newZoom;
            if (newZoom === 1) {
                editor.minimap.panX = 0;
                editor.minimap.panY = 0;
                delete editor.minimap._cachedBase;
            }
            if (window.MinimapRender) window.MinimapRender.invalidateCache();
            editor.renderMinimap();
        });
        if (mmZoomReset) mmZoomReset.addEventListener('click', (e) => {
            e.stopPropagation();
            editor.minimap.zoom = 1;
            editor.minimap.panX = 0;
            editor.minimap.panY = 0;
            delete editor.minimap._cachedBase;
            if (window.MinimapRender) window.MinimapRender.invalidateCache();
            editor.renderMinimap();
        });

        // Initial render
        setTimeout(() => editor.renderMinimap(), 100);
    },

    /**
     * Apply linked zoom: minimap zoom changes also zoom the main canvas
     * proportionally, keeping the view centered on the same world point.
     * @param {Object} editor - TopologyEditor instance
     * @param {number} factor - Zoom multiplier (>1 = zoom in, <1 = zoom out)
     */
    _applyLinkedZoom(editor, factor) {
        if (factor === 1) return;
        const cx = (editor.canvasW || editor.canvas.width) / 2;
        const cy = (editor.canvasH || editor.canvas.height) / 2;
        const worldCX = (cx - editor.panOffset.x) / editor.zoom;
        const worldCY = (cy - editor.panOffset.y) / editor.zoom;
        editor.zoom = Math.max(0.05, Math.min(3, editor.zoom * factor));
        editor.panOffset.x = cx - worldCX * editor.zoom;
        editor.panOffset.y = cy - worldCY * editor.zoom;
    },

    /**
     * Start the smooth drag animation loop
     * @param {Object} editor - TopologyEditor instance
     */
    startDragLoop(editor) {
        if (editor.minimap.animationId) return;
        
        const loop = () => {
            if (!editor.minimap.isDragging) return;
            
            if (editor.minimap.targetPan) {
                // Smooth interpolation towards target
                const lerpFactor = 0.35;
                const dx = editor.minimap.targetPan.x - editor.panOffset.x;
                const dy = editor.minimap.targetPan.y - editor.panOffset.y;
                
                // Only update if there's meaningful movement
                if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
                    editor.panOffset.x += dx * lerpFactor;
                    editor.panOffset.y += dy * lerpFactor;
                    editor.draw();
                    editor.updateHud();
                    editor.updateScrollbars();
                }
            }
            
            editor.minimap.animationId = requestAnimationFrame(loop);
        };
        
        editor.minimap.animationId = requestAnimationFrame(loop);
    },

    /**
     * Stop the drag animation loop
     * @param {Object} editor - TopologyEditor instance
     */
    stopDragLoop(editor) {
        if (editor.minimap.animationId) {
            cancelAnimationFrame(editor.minimap.animationId);
            editor.minimap.animationId = null;
        }
        editor.minimap.targetPan = null;
    },

    /**
     * Update target pan position during drag
     * @param {Object} editor - TopologyEditor instance
     * @param {Event} e - Mouse event
     */
    updateDragTarget(editor, e) {
        if (!editor.minimap || !editor.minimap.isDragging) return;
        
        const rect = editor.minimap.canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;
        
        // Use frozen bounds from drag start to prevent jitter
        const bounds = editor.minimap._dragBounds || this.getBounds(editor);
        if (!bounds || bounds.scale <= 0) return;
        
        // Convert mouse position to world coordinates
        const worldX = bounds.minX + (clickX - bounds.offsetX) / bounds.scale;
        const worldY = bounds.minY + (clickY - bounds.offsetY) / bounds.scale;
        
        // Calculate target pan to center on this point
        editor.minimap.targetPan = {
            x: (editor.canvasW || editor.canvas.width) / 2 - worldX * editor.zoom,
            y: (editor.canvasH || editor.canvas.height) / 2 - worldY * editor.zoom
        };
    },

    /**
     * Immediate navigation for initial click
     * @param {Object} editor - TopologyEditor instance
     * @param {Event} e - Mouse event
     */
    navigateFromDrag(editor, e) {
        if (!editor.minimap) return;
        
        const rect = editor.minimap.canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;
        
        // Use frozen bounds from drag start to prevent jitter
        const bounds = editor.minimap._dragBounds || this.getBounds(editor);
        if (!bounds || bounds.scale <= 0) return;
        
        // Convert click to world coordinates
        const worldX = bounds.minX + (clickX - bounds.offsetX) / bounds.scale;
        const worldY = bounds.minY + (clickY - bounds.offsetY) / bounds.scale;
        
        // Set target for smooth follow
        editor.minimap.targetPan = {
            x: (editor.canvasW || editor.canvas.width) / 2 - worldX * editor.zoom,
            y: (editor.canvasH || editor.canvas.height) / 2 - worldY * editor.zoom
        };
        
        const instantFactor = 0.7;
        editor.panOffset.x += (editor.minimap.targetPan.x - editor.panOffset.x) * instantFactor;
        editor.panOffset.y += (editor.minimap.targetPan.y - editor.panOffset.y) * instantFactor;
        
        editor.draw();
        editor.updateHud();
        editor.updateScrollbars();
    },

    /**
     * Toggle minimap visibility
     * @param {Object} editor - TopologyEditor instance
     */
    toggle(editor) {
        if (!editor.minimap) return;
        
        editor.minimap.visible = !editor.minimap.visible;
        const toggleBtn = document.getElementById('btn-toggle-minimap');
        
        if (editor.minimap.visible) {
            editor.minimap.container.style.display = 'block';
            if (toggleBtn) toggleBtn.classList.add('minimap-on');
            editor.renderMinimap();
        } else {
            editor.minimap.container.style.display = 'none';
            if (toggleBtn) toggleBtn.classList.remove('minimap-on');
        }
        
        // Save preference
        localStorage.setItem('minimapVisible', editor.minimap.visible);
    },

    /**
     * Get the combined bounds for minimap
     * @param {Object} editor - TopologyEditor instance
     * @returns {Object} Bounds object
     */
    getBounds(editor) {
        const canvasWidth = 188;
        const canvasHeight = 100;

        // Main canvas viewport in world coordinates
        const viewLeft = (0 - editor.panOffset.x) / editor.zoom;
        const viewTop = (0 - editor.panOffset.y) / editor.zoom;
        const viewRight = ((editor.canvasW || editor.canvas.width) - editor.panOffset.x) / editor.zoom;
        const viewBottom = ((editor.canvasH || editor.canvas.height) - editor.panOffset.y) / editor.zoom;

        const topologyBounds = this.getTopologyBounds(editor);
        const mmZoom = (editor.minimap && editor.minimap.zoom) || 1;
        const padding = 50;

        let minX, maxX, minY, maxY;

        if (mmZoom > 1 && topologyBounds) {
            // When zoomed in: cache the combined bounds at first zoom-in
            // to prevent jitter from viewport movement. Expand (never shrink)
            // if viewport moves beyond cached area.
            if (!editor.minimap._cachedBase) {
                editor.minimap._cachedBase = {
                    minX: Math.min(topologyBounds.minX, viewLeft) - padding,
                    maxX: Math.max(topologyBounds.maxX, viewRight) + padding,
                    minY: Math.min(topologyBounds.minY, viewTop) - padding,
                    maxY: Math.max(topologyBounds.maxY, viewBottom) + padding,
                };
            }
            const cb = editor.minimap._cachedBase;
            cb.minX = Math.min(cb.minX, viewLeft - padding);
            cb.maxX = Math.max(cb.maxX, viewRight + padding);
            cb.minY = Math.min(cb.minY, viewTop - padding);
            cb.maxY = Math.max(cb.maxY, viewBottom + padding);
            minX = cb.minX; maxX = cb.maxX;
            minY = cb.minY; maxY = cb.maxY;
        } else if (topologyBounds) {
            minX = Math.min(topologyBounds.minX, viewLeft) - padding;
            maxX = Math.max(topologyBounds.maxX, viewRight) + padding;
            minY = Math.min(topologyBounds.minY, viewTop) - padding;
            maxY = Math.max(topologyBounds.maxY, viewBottom) + padding;
        } else {
            minX = viewLeft - padding;
            maxX = viewRight + padding;
            minY = viewTop - padding;
            maxY = viewBottom + padding;
        }

        const boundsWidth = maxX - minX;
        const boundsHeight = maxY - minY;

        const scaleX = canvasWidth / boundsWidth;
        const scaleY = canvasHeight / boundsHeight;
        let scale = Math.min(scaleX, scaleY);

        let offsetX = (canvasWidth - boundsWidth * scale) / 2;
        let offsetY = (canvasHeight - boundsHeight * scale) / 2;

        if (mmZoom > 1) {
            scale *= mmZoom;
            const panX = (editor.minimap && editor.minimap.panX) || 0;
            const panY = (editor.minimap && editor.minimap.panY) || 0;
            const vcx = (viewLeft + viewRight) / 2 + panX;
            const vcy = (viewTop + viewBottom) / 2 + panY;
            offsetX = canvasWidth / 2 - (vcx - minX) * scale;
            offsetY = canvasHeight / 2 - (vcy - minY) * scale;
        }

        return {
            minX, maxX, minY, maxY,
            boundsWidth, boundsHeight,
            scale, offsetX, offsetY,
            canvasWidth, canvasHeight,
            viewLeft, viewTop, viewRight, viewBottom
        };
    },

    /**
     * Get bounding box of all objects
     * @param {Object} editor - TopologyEditor instance
     * @returns {Object|null} Bounds or null if no objects
     */
    getTopologyBounds(editor) {
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        let hasObjects = false;
        
        for (const obj of editor.objects) {
            if (obj.type === 'device') {
                const r = obj.radius || 30;
                minX = Math.min(minX, obj.x - r);
                maxX = Math.max(maxX, obj.x + r);
                minY = Math.min(minY, obj.y - r);
                maxY = Math.max(maxY, obj.y + r);
                hasObjects = true;
            } else if (obj.type === 'text') {
                minX = Math.min(minX, obj.x - 50);
                maxX = Math.max(maxX, obj.x + 50);
                minY = Math.min(minY, obj.y - 20);
                maxY = Math.max(maxY, obj.y + 20);
                hasObjects = true;
            } else if (obj.type === 'link' || obj.type === 'unbound') {
                const endpoints = editor.getLinkEndpoints(obj);
                if (endpoints) {
                    minX = Math.min(minX, endpoints.startX, endpoints.endX);
                    maxX = Math.max(maxX, endpoints.startX, endpoints.endX);
                    minY = Math.min(minY, endpoints.startY, endpoints.endY);
                    maxY = Math.max(maxY, endpoints.startY, endpoints.endY);
                    hasObjects = true;
                }
            }
        }
        
        if (!hasObjects) return null;
        
        return { minX, maxX, minY, maxY };
    }
};

console.log('[topology-minimap.js] MinimapModule loaded');
