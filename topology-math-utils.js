/**
 * topology-math-utils.js - Math and Animation Utility Functions
 * 
 * Extracted from topology.js for modular architecture.
 * Contains mathematical functions for interpolation, coordinate conversion, etc.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.MathUtils = {

    /**
     * Linear interpolation for smooth position updates
     * @param {number} current - Current value
     * @param {number} target - Target value
     * @param {number} factor - Interpolation factor (0.1 = very smooth, 0.3 = responsive, 0.5 = quick)
     * @returns {number} Interpolated value
     */
    lerp(current, target, factor = 0.15) {
        const diff = target - current;
        // Snap to target if very close (avoid endless tiny movements)
        if (Math.abs(diff) < 0.5) {
            return target;
        }
        return current + diff * factor;
    },

    /**
     * Interpolate a point (x, y) toward target
     * @param {{x: number, y: number}} current - Current point
     * @param {{x: number, y: number}} target - Target point
     * @param {number} factor - Interpolation factor
     * @returns {{x: number, y: number}} Interpolated point
     */
    lerpPoint(current, target, factor = 0.15) {
        return {
            x: this.lerp(current.x, target.x, factor),
            y: this.lerp(current.y, target.y, factor)
        };
    },

    /**
     * Calculate distance between two touch points
     * @param {Touch} touch1 - First touch point
     * @param {Touch} touch2 - Second touch point
     * @returns {number} Distance between touches
     */
    getDistance(touch1, touch2) {
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    },

    /**
     * Calculate center point between two touch points
     * @param {Touch} touch1 - First touch point
     * @param {Touch} touch2 - Second touch point
     * @returns {{x: number, y: number}} Center point
     */
    getTwoFingerCenter(touch1, touch2) {
        return {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };
    },

    /**
     * Calculate distance from a point to a line segment
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {{x: number, y: number}} lineStart - Line start point
     * @param {{x: number, y: number}} lineEnd - Line end point
     * @returns {number} Distance to line
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
     * Clamp a value between min and max
     * @param {number} value - Value to clamp
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @returns {number} Clamped value
     */
    clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    },

    /**
     * Convert degrees to radians
     * @param {number} degrees - Angle in degrees
     * @returns {number} Angle in radians
     */
    degToRad(degrees) {
        return degrees * Math.PI / 180;
    },

    /**
     * Convert radians to degrees
     * @param {number} radians - Angle in radians
     * @returns {number} Angle in degrees
     */
    radToDeg(radians) {
        return radians * 180 / Math.PI;
    },

    /**
     * Calculate angle between two points
     * @param {{x: number, y: number}} p1 - First point
     * @param {{x: number, y: number}} p2 - Second point
     * @returns {number} Angle in radians
     */
    angleBetween(p1, p2) {
        return Math.atan2(p2.y - p1.y, p2.x - p1.x);
    },

    /**
     * Calculate distance between two points
     * @param {{x: number, y: number}} p1 - First point
     * @param {{x: number, y: number}} p2 - Second point
     * @returns {number} Distance
     */
    distanceBetween(p1, p2) {
        return Math.hypot(p2.x - p1.x, p2.y - p1.y);
    },

    /**
     * Convert hex color to rgba
     * @param {string} hex - Hex color string (e.g., "#ff0000")
     * @param {number} alpha - Alpha value (0-1)
     * @returns {string} RGBA color string
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    /**
     * Check if a point is inside a triangle using barycentric coordinates.
     * Used for pixel-accurate arrow tip hitbox detection.
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} v1x - Vertex 1 X (tip)
     * @param {number} v1y - Vertex 1 Y (tip)
     * @param {number} v2x - Vertex 2 X (base left)
     * @param {number} v2y - Vertex 2 Y (base left)
     * @param {number} v3x - Vertex 3 X (base right)
     * @param {number} v3y - Vertex 3 Y (base right)
     * @returns {boolean} True if point is inside the triangle
     */
    isPointInTriangle(px, py, v1x, v1y, v2x, v2y, v3x, v3y) {
        const denom = (v2y - v3y) * (v1x - v3x) + (v3x - v2x) * (v1y - v3y);
        if (Math.abs(denom) < 0.0001) return false; // Degenerate triangle
        const a = ((v2y - v3y) * (px - v3x) + (v3x - v2x) * (py - v3y)) / denom;
        const b = ((v3y - v1y) * (px - v3x) + (v1x - v3x) * (py - v3y)) / denom;
        const c = 1 - a - b;
        return a >= 0 && a <= 1 && b >= 0 && b <= 1 && c >= 0 && c <= 1;
    }
};

console.log('[topology-math-utils.js] MathUtils loaded');
