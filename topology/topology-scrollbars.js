/**
 * topology-scrollbars.js - Scrollbar Navigation Module
 * 
 * Extracted from topology.js for modular architecture.
 * Contains scrollbar setup and update functions.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.ScrollbarsModule = {

    /**
     * Setup scrollbars with event handlers
     * @param {Object} editor - TopologyEditor instance
     */
    setup(editor) {
        const vScrollbar = document.getElementById('vertical-scrollbar');
        const hScrollbar = document.getElementById('horizontal-scrollbar');
        const vThumb = document.getElementById('vertical-thumb');
        const hThumb = document.getElementById('horizontal-thumb');
        
        // Early return if elements don't exist yet
        if (!vScrollbar || !hScrollbar || !vThumb || !hThumb) {
            console.warn('Scrollbar elements not found, skipping setup');
            return;
        }
        
        // Vertical scrollbar (with touchpad support)
        const vThumbDown = (e) => {
            e.stopPropagation();
            editor.draggingScrollbar = 'vertical';
            editor.scrollbarDragStart = {
                y: e.clientY,
                panOffset: editor.panOffset.y
            };
        };
        vThumb.addEventListener('mousedown', vThumbDown);
        if (window.PointerEvent) {
            vThumb.addEventListener('pointerdown', vThumbDown);
        }
        
        // Horizontal scrollbar (with touchpad support)
        const hThumbDown = (e) => {
            e.stopPropagation();
            editor.draggingScrollbar = 'horizontal';
            editor.scrollbarDragStart = {
                x: e.clientX,
                panOffset: editor.panOffset.x
            };
        };
        hThumb.addEventListener('mousedown', hThumbDown);
        if (window.PointerEvent) {
            hThumb.addEventListener('pointerdown', hThumbDown);
        }
        
        // Global mouse/pointer events for scrollbar dragging
        const handleScrollbarMove = (e) => {
            if (editor.draggingScrollbar === 'vertical') {
                const deltaY = e.clientY - editor.scrollbarDragStart.y;
                const scrollbarHeight = vScrollbar.clientHeight;
                const thumbHeight = vThumb.clientHeight;
                const maxScroll = scrollbarHeight - thumbHeight;
                const scrollRatio = deltaY / maxScroll;
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, editor.zoom);
                const panRange = baseRange * zoomFactor;
                editor.panOffset.y = editor.scrollbarDragStart.panOffset + (scrollRatio * panRange * 2);
                editor.savePanOffset();
                editor.updateScrollbars();
                editor.draw();
            } else if (editor.draggingScrollbar === 'horizontal') {
                const deltaX = e.clientX - editor.scrollbarDragStart.x;
                const scrollbarWidth = hScrollbar.clientWidth;
                const thumbWidth = hThumb.clientWidth;
                const maxScroll = scrollbarWidth - thumbWidth;
                const scrollRatio = deltaX / maxScroll;
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, editor.zoom);
                const panRange = baseRange * zoomFactor;
                editor.panOffset.x = editor.scrollbarDragStart.panOffset + (scrollRatio * panRange * 2);
                editor.savePanOffset();
                editor.updateScrollbars();
                editor.draw();
            }
        };
        
        document.addEventListener('mousemove', handleScrollbarMove);
        if (window.PointerEvent) {
            document.addEventListener('pointermove', handleScrollbarMove);
        }
        
        // Mouse alignment: Click scrollbar track to jump thumb to mouse position
        vScrollbar.addEventListener('click', (e) => {
            if (e.target === vScrollbar) { // Clicked track, not thumb
                const rect = vScrollbar.getBoundingClientRect();
                const clickY = e.clientY - rect.top;
                const scrollbarHeight = vScrollbar.clientHeight;
                const thumbHeight = vThumb.clientHeight;
                
                // Center thumb at click position
                const newThumbTop = clickY - thumbHeight / 2;
                const maxScroll = scrollbarHeight - thumbHeight;
                const scrollRatio = (newThumbTop / maxScroll) * 2 - 1; // -1 to 1
                
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, editor.zoom);
                const panRange = baseRange * zoomFactor;
                editor.panOffset.y = scrollRatio * panRange;
                editor.savePanOffset();
                editor.updateScrollbars();
                editor.draw();
                editor.updateHud();
            }
        });
        
        hScrollbar.addEventListener('click', (e) => {
            if (e.target === hScrollbar) { // Clicked track, not thumb
                const rect = hScrollbar.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const scrollbarWidth = hScrollbar.clientWidth;
                const thumbWidth = hThumb.clientWidth;
                
                // Center thumb at click position
                const newThumbLeft = clickX - thumbWidth / 2;
                const maxScroll = scrollbarWidth - thumbWidth;
                const scrollRatio = (newThumbLeft / maxScroll) * 2 - 1; // -1 to 1
                
                // Use same dynamic range as updateScrollbars
                const baseRange = 2000;
                const zoomFactor = Math.max(1, editor.zoom);
                const panRange = baseRange * zoomFactor;
                editor.panOffset.x = scrollRatio * panRange;
                editor.savePanOffset();
                editor.updateScrollbars();
                editor.draw();
                editor.updateHud();
            }
        });
        
        const handleScrollbarUp = () => {
            editor.draggingScrollbar = null;
            editor.scrollbarDragStart = null;
        };
        
        document.addEventListener('mouseup', handleScrollbarUp);
        if (window.PointerEvent) {
            document.addEventListener('pointerup', handleScrollbarUp);
        }
    },

    /**
     * Update scrollbar thumb positions based on current pan
     * @param {Object} editor - TopologyEditor instance
     */
    update(editor) {
        const vThumb = document.getElementById('vertical-thumb');
        const hThumb = document.getElementById('horizontal-thumb');
        const vScrollbar = document.getElementById('vertical-scrollbar');
        const hScrollbar = document.getElementById('horizontal-scrollbar');
        
        if (!vThumb || !hThumb || !vScrollbar || !hScrollbar) return;
        
        // ENHANCED: Dynamic range based on zoom for better representation
        const baseRange = 2000;
        const zoomFactor = Math.max(1, editor.zoom);
        const panRange = baseRange * zoomFactor;
        
        // Vertical scrollbar - smooth position calculation
        const vMax = vScrollbar.clientHeight - vThumb.clientHeight;
        const vRatio = Math.max(-1, Math.min(1, editor.panOffset.y / panRange));
        const vPos = (vRatio + 1) / 2 * vMax;
        const vPosClamped = Math.max(0, Math.min(vMax, vPos));
        
        // SMOOTH: Use transform for GPU acceleration
        vThumb.style.transform = `translateY(${vPosClamped}px)`;
        vThumb.style.top = '0';
        
        // Horizontal scrollbar - smooth position calculation
        const hMax = hScrollbar.clientWidth - hThumb.clientWidth;
        const hRatio = Math.max(-1, Math.min(1, editor.panOffset.x / panRange));
        const hPos = (hRatio + 1) / 2 * hMax;
        const hPosClamped = Math.max(0, Math.min(hMax, hPos));
        
        // SMOOTH: Use transform for GPU acceleration
        hThumb.style.transform = `translateX(${hPosClamped}px)`;
        hThumb.style.left = '0';
        
        // Update minimap to reflect current viewport
        editor.renderMinimap();
    }
};

console.log('[topology-scrollbars.js] ScrollbarsModule loaded');
