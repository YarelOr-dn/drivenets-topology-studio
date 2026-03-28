/**
 * topology-touch.js - Touch Gesture Handling Module
 * 
 * Extracted from topology.js for modular architecture.
 * Contains touch gesture handling for multi-touch devices.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.TouchHandler = {

    /**
     * Handle touch start event
     * @param {Object} editor - TopologyEditor instance
     * @param {TouchEvent} e - Touch event
     */
    handleTouchStart(editor, e) {
        e.preventDefault();
        
        // Track gesture state
        editor.gestureState.fingerCount = e.touches.length;
        editor.gestureState.gestureStartTime = Date.now();
        editor.gestureState.gestureMoved = false;
        
        if (e.touches.length > 0) {
            const pos = editor.getTouchPos(e.touches[0]);
            editor.gestureState.gestureStartPos = { x: pos.x, y: pos.y };
        }
        
        // Log gesture start
        if (editor.debugger && e.touches.length > 1) {
            editor.debugger.logInfo(`👆 ${e.touches.length}-finger gesture started`);
        }
        
        if (e.touches.length === 1) {
            // Single finger - normal touch/tap/drag
            editor.handleMouseDown({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
        } else if (e.touches.length === 2) {
            // Two-finger gesture - prepare for pinch or pan
            editor.pinching = true;
            editor.lastPinchDistance = editor.getDistance(e.touches[0], e.touches[1]);
            editor.lastTwoFingerCenter = editor.getTwoFingerCenter(e.touches[0], e.touches[1]);
            editor.gestureState.lastGestureType = '2-finger-pinch';
        } else if (e.touches.length === 3) {
            // Three-finger gesture
            const pos = editor.getTouchPos(e.touches[0]);
            editor.gestureState.lastGestureType = '3-finger-tap';
            editor.gestureState.stored3FingerPos = pos;
            return;
        } else if (e.touches.length === 4) {
            // Four-finger gesture - toggle presentation mode
            editor.gestureState.lastGestureType = '4-finger-swipe';
            
            if (editor.debugger) {
                editor.debugger.logInfo(`👆👆👆👆 4-finger gesture: detected`);
            }
            return;
        }
    },

    /**
     * Process 3-finger tap gesture
     * @param {Object} editor - TopologyEditor instance
     */
    process3FingerTap(editor) {
        // DISABLED: 3-finger tap functionality
        if (editor.debugger) {
            editor.debugger.logInfo(`👆 3-finger tap detected but disabled`);
        }
        editor.gestureState.stored3FingerPos = null;
    },

    /**
     * Handle touch move event
     * @param {Object} editor - TopologyEditor instance
     * @param {TouchEvent} e - Touch event
     */
    handleTouchMove(editor, e) {
        e.preventDefault();
        
        // Track if gesture has moved
        if (!editor.gestureState.gestureMoved && editor.gestureState.gestureStartPos && e.touches.length > 0) {
            const currentPos = editor.getTouchPos(e.touches[0]);
            const dx = Math.abs(currentPos.x - editor.gestureState.gestureStartPos.x);
            const dy = Math.abs(currentPos.y - editor.gestureState.gestureStartPos.y);
            
            if (dx > editor.gestureState.moveThreshold || dy > editor.gestureState.moveThreshold) {
                editor.gestureState.gestureMoved = true;
                
                if (editor.debugger && e.touches.length >= 3) {
                    editor.debugger.logInfo(`👆 ${e.touches.length}-finger SWIPE detected`);
                }
            }
        }
        
        if (e.touches.length === 1) {
            // Single finger - normal drag
            editor.handleMouseMove({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
        } else if (e.touches.length === 2 && editor.pinching) {
            // Two fingers - pinch zoom and pan
            const currentDistance = editor.getDistance(e.touches[0], e.touches[1]);
            const currentCenter = editor.getTwoFingerCenter(e.touches[0], e.touches[1]);
            
            // Pinch zoom
            if (editor.lastPinchDistance) {
                const delta = currentDistance - editor.lastPinchDistance;
                if (Math.abs(delta) > 2) {
                    const zoomFactor = currentDistance / editor.lastPinchDistance;
                    const oldZoom = editor.zoom;
                    const newZoom = Math.max(0.05, Math.min(3, editor.zoom * zoomFactor));
                    
                    if (!editor._pinchRect || !editor._pinchRectTs || performance.now() - editor._pinchRectTs > 500) {
                        editor._pinchRect = editor.canvas.getBoundingClientRect();
                        editor._pinchRectTs = performance.now();
                    }
                    const rect = editor._pinchRect;
                    const centerX = currentCenter.x - rect.left;
                    const centerY = currentCenter.y - rect.top;
                    
                    const worldX = (centerX - editor.panOffset.x) / oldZoom;
                    const worldY = (centerY - editor.panOffset.y) / oldZoom;
                    
                    editor.zoom = newZoom;
                    
                    editor.panOffset.x = centerX - worldX * newZoom;
                    editor.panOffset.y = centerY - worldY * newZoom;
                    
                    editor.lastPinchDistance = currentDistance;
                    editor._viewportOnly = true;
                    if (!editor._pinchRafId) {
                        editor._pinchRafId = requestAnimationFrame(() => {
                            editor._pinchRafId = null;
                            editor.draw();
                            editor.updateZoomIndicator();
                        });
                    }
                }
            }
            
            // Two-finger panning
            if (editor.lastTwoFingerCenter) {
                const deltaX = currentCenter.x - editor.lastTwoFingerCenter.x;
                const deltaY = currentCenter.y - editor.lastTwoFingerCenter.y;
                
                if (Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1) {
                    editor.panOffset.x += deltaX;
                    editor.panOffset.y += deltaY;
                    editor._viewportOnly = true;
                    if (!editor._pinchRafId) {
                        editor._pinchRafId = requestAnimationFrame(() => {
                            editor._pinchRafId = null;
                            editor.draw();
                            editor.updateScrollbars();
                        });
                    }
                }
            }
            
            editor.lastTwoFingerCenter = currentCenter;
        }
    },

    /**
     * Handle touch end event
     * @param {Object} editor - TopologyEditor instance
     * @param {TouchEvent} e - Touch event
     */
    handleTouchEnd(editor, e) {
        e.preventDefault();
        
        const gestureDuration = Date.now() - editor.gestureState.gestureStartTime;
        const wasTap = !editor.gestureState.gestureMoved && gestureDuration < editor.gestureState.tapThreshold;
        const lastFingerCount = editor.gestureState.fingerCount;
        
        // Double-tap detection for single-finger taps
        if (wasTap && lastFingerCount === 1 && e.changedTouches.length > 0) {
            this._handleDoubleTap(editor, e);
        }
        
        // 4-finger tap handling
        if (wasTap && lastFingerCount === 4 && editor.gestureState.lastGestureType === '4-finger-swipe') {
            this.toggle4FingerMode(editor);
            
            if (editor.debugger) {
                editor.debugger.logSuccess(`✓ 4-finger TAP confirmed: UI toggle`);
            }
        }
        
        // Standard touch cleanup
        if (e.touches.length === 0) {
            editor.pinching = false;
            editor.lastPinchDistance = null;
            editor.lastTwoFingerCenter = null;
            editor._pinchRect = null;
            editor.gestureState.fingerCount = 0;
            editor.savePanOffset();
            editor.handleMouseUp(e);
        } else if (e.touches.length === 1) {
            editor.pinching = false;
            editor.lastPinchDistance = null;
            editor.lastTwoFingerCenter = null;
            editor.gestureState.fingerCount = e.touches.length;
        } else {
            editor.gestureState.fingerCount = e.touches.length;
        }
    },

    /**
     * Handle double-tap gesture
     * @param {Object} editor - TopologyEditor instance
     * @param {TouchEvent} e - Touch event
     */
    _handleDoubleTap(editor, e) {
        const now = Date.now();
        const pos = editor.getTouchPos(e.changedTouches[0]);
        
        if (editor.lastTouchTapTime && editor.lastTouchTapPos) {
            const timeDiff = now - editor.lastTouchTapTime;
            const dx = pos.x - editor.lastTouchTapPos.x;
            const dy = pos.y - editor.lastTouchTapPos.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            
            if (timeDiff < editor.doubleTapThreshold && dist < editor.doubleTapDistanceThreshold) {
                // Double-tap detected
                let clickedObject = editor.findObjectAt(pos.x, pos.y);
                
                // Check rotated text hitbox
                if (!clickedObject || clickedObject.type !== 'text') {
                    const textInHitbox = editor.objects.find(obj => {
                        if (obj.type !== 'text') return false;
                        
                        editor.ctx.save();
                        editor.ctx.font = `${obj.fontSize}px Arial`;
                        const metrics = editor.ctx.measureText(obj.text || 'Text');
                        const w = metrics.width;
                        const h = parseInt(obj.fontSize);
                        editor.ctx.restore();
                        
                        const rectW = w + 10;
                        const rectH = h + 10;
                        
                        const angle = obj.rotation * Math.PI / 180;
                        const tdx = pos.x - obj.x;
                        const tdy = pos.y - obj.y;
                        
                        const localX = tdx * Math.cos(-angle) - tdy * Math.sin(-angle);
                        const localY = tdx * Math.sin(-angle) + tdy * Math.cos(-angle);
                        
                        return Math.abs(localX) <= rectW/2 && Math.abs(localY) <= rectH/2;
                    });
                    
                    if (textInHitbox) clickedObject = textInHitbox;
                }
                
                if (clickedObject && clickedObject.type === 'text') {
                    editor.selectedObject = clickedObject;
                    editor.selectedObjects = [clickedObject];
                    editor.draw();
                    
                    setTimeout(() => {
                        editor.showTextEditor(clickedObject);
                    }, 50);
                    
                    editor.lastTouchTapTime = 0;
                    editor.lastTouchTapPos = null;
                    return;
                } else if (clickedObject && clickedObject.type === 'device') {
                    editor.setMode('link');
                    editor.linking = true;
                    editor.linkStart = clickedObject;
                    editor.lastTouchTapTime = 0;
                    editor.lastTouchTapPos = null;
                    editor.draw();
                    return;
                } else if (!clickedObject) {
                    if (editor.currentTool === 'text') {
                        editor.setMode('base');
                        editor.lastTouchTapTime = 0;
                        editor.lastTouchTapPos = null;
                        return;
                    }
                    editor.lastTouchTapTime = now;
                    editor.lastTouchTapPos = pos;
                } else {
                    editor.lastTouchTapTime = 0;
                    editor.lastTouchTapPos = null;
                }
            } else {
                editor.lastTouchTapTime = now;
                editor.lastTouchTapPos = pos;
            }
        } else {
            editor.lastTouchTapTime = now;
            editor.lastTouchTapPos = pos;
        }
    },

    /**
     * Toggle 4-finger presentation mode
     * @param {Object} editor - TopologyEditor instance
     */
    toggle4FingerMode(editor) {
        const topBar = document.querySelector('.top-bar');
        const leftToolbar = document.getElementById('left-toolbar');
        
        const topBarHidden = topBar && topBar.classList.contains('collapsed');
        const leftToolbarHidden = leftToolbar && leftToolbar.classList.contains('collapsed');
        
        if (topBarHidden || leftToolbarHidden) {
            if (topBar) topBar.classList.remove('collapsed');
            if (leftToolbar) leftToolbar.classList.remove('collapsed');
            editor.syncBarCollapseState?.();
            if (editor.debugger) {
                editor.debugger.logSuccess(`👆👆👆👆 4-finger tap: SHOW all UI`);
            }
        } else {
            if (topBar) topBar.classList.add('collapsed');
            if (leftToolbar) leftToolbar.classList.add('collapsed');
            editor.syncBarCollapseState?.();
            if (editor.debugger) {
                editor.debugger.logSuccess(`👆👆👆👆 4-finger tap: HIDE all UI`);
            }
        }

        setTimeout(() => {
            editor.resizeCanvas();
            editor.draw();
        }, 300);
    }
};

console.log('[topology-touch.js] TouchHandler module loaded');
