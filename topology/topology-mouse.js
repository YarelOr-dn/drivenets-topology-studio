/**
 * topology-mouse.js - Mouse Event Handler Coordinator
 * 
 * Thin coordinator that delegates to individual handler modules:
 * - topology-mouse-down.js (MouseDownHandler)
 * - topology-mouse-move.js (MouseMoveHandler)
 * - topology-mouse-up.js (MouseUpHandler)
 */

'use strict';

window.MouseHandler = {
    handleMouseDown(editor, e) {
        if (window.MouseDownHandler) {
            return window.MouseDownHandler.handleMouseDown(editor, e);
        }
    },

    handleMouseMove(editor, e) {
        if (window.MouseMoveHandler) {
            return window.MouseMoveHandler.handleMouseMove(editor, e);
        }
    },

    handleMouseUp(editor, e) {
        if (window.MouseUpHandler) {
            return window.MouseUpHandler.handleMouseUp(editor, e);
        }
    },

    handleDoubleClick(editor, e) {
        if (window.MouseDownHandler) {
            return window.MouseDownHandler.handleDoubleClick(editor, e);
        }
    }
};

console.log('[topology-mouse.js] MouseHandler coordinator loaded');
