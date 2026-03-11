// ============================================================================
// TOPOLOGY GEOMETRY UTILITIES
// ============================================================================
// Pure geometry functions for hit detection, distance calculations, and
// coordinate transformations. These are stateless utility functions.
//
// Usage:
//   TopologyGeometry.distanceToLine(px, py, lineStart, lineEnd);
//   TopologyGeometry.isPointInRect(x, y, rect);
//   TopologyGeometry.pointOnBezier(t, p0, p1, p2, p3);
// ============================================================================

const TopologyGeometry = {
    
    // ========== DISTANCE CALCULATIONS ==========
    
    /**
     * Calculate distance from a point to a line segment
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {object} lineStart - Line start {x, y}
     * @param {object} lineEnd - Line end {x, y}
     * @returns {number} Distance to line segment
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
     * Calculate distance between two points
     * @param {object} p1 - First point {x, y}
     * @param {object} p2 - Second point {x, y}
     * @returns {number} Distance
     */
    distanceBetweenPoints(p1, p2) {
        return Math.hypot(p2.x - p1.x, p2.y - p1.y);
    },
    
    /**
     * Calculate squared distance (faster when only comparing)
     * @param {object} p1 - First point {x, y}
     * @param {object} p2 - Second point {x, y}
     * @returns {number} Squared distance
     */
    distanceSquared(p1, p2) {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        return dx * dx + dy * dy;
    },
    
    // ========== POINT-IN-SHAPE TESTS ==========
    
    /**
     * Check if point is inside a rectangle
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} rx - Rect X (top-left)
     * @param {number} ry - Rect Y (top-left)
     * @param {number} rw - Rect width
     * @param {number} rh - Rect height
     * @returns {boolean}
     */
    isPointInRect(px, py, rx, ry, rw, rh) {
        return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
    },
    
    /**
     * Check if point is inside a circle
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} cx - Circle center X
     * @param {number} cy - Circle center Y
     * @param {number} r - Circle radius
     * @returns {boolean}
     */
    isPointInCircle(px, py, cx, cy, r) {
        const dx = px - cx;
        const dy = py - cy;
        return (dx * dx + dy * dy) <= (r * r);
    },
    
    /**
     * Check if point is inside an ellipse
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} cx - Ellipse center X
     * @param {number} cy - Ellipse center Y
     * @param {number} rx - Ellipse X radius
     * @param {number} ry - Ellipse Y radius
     * @param {number} rotation - Rotation in radians
     * @returns {boolean}
     */
    isPointInEllipse(px, py, cx, cy, rx, ry, rotation = 0) {
        // Transform point to ellipse-local coordinates
        const dx = px - cx;
        const dy = py - cy;
        const cos = Math.cos(-rotation);
        const sin = Math.sin(-rotation);
        const localX = dx * cos - dy * sin;
        const localY = dx * sin + dy * cos;
        
        // Check if inside ellipse
        return (localX * localX) / (rx * rx) + (localY * localY) / (ry * ry) <= 1;
    },
    
    /**
     * Check if point is inside a rotated rectangle
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} cx - Rect center X
     * @param {number} cy - Rect center Y
     * @param {number} halfW - Half width
     * @param {number} halfH - Half height
     * @param {number} rotation - Rotation in radians
     * @returns {boolean}
     */
    isPointInRotatedRect(px, py, cx, cy, halfW, halfH, rotation = 0) {
        // Transform point to rect-local coordinates
        const dx = px - cx;
        const dy = py - cy;
        const cos = Math.cos(-rotation);
        const sin = Math.sin(-rotation);
        const localX = dx * cos - dy * sin;
        const localY = dx * sin + dy * cos;
        
        return Math.abs(localX) <= halfW && Math.abs(localY) <= halfH;
    },
    
    // ========== BEZIER CURVES ==========
    
    /**
     * Calculate point on a cubic Bezier curve
     * @param {number} t - Parameter (0-1)
     * @param {object} p0 - Start point {x, y}
     * @param {object} p1 - Control point 1 {x, y}
     * @param {object} p2 - Control point 2 {x, y}
     * @param {object} p3 - End point {x, y}
     * @returns {object} Point {x, y}
     */
    pointOnBezier(t, p0, p1, p2, p3) {
        const t2 = t * t;
        const t3 = t2 * t;
        const mt = 1 - t;
        const mt2 = mt * mt;
        const mt3 = mt2 * mt;
        
        return {
            x: mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x,
            y: mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
        };
    },
    
    /**
     * Calculate tangent (derivative) of cubic Bezier at point t
     * @param {number} t - Parameter (0-1)
     * @param {object} p0 - Start point {x, y}
     * @param {object} p1 - Control point 1 {x, y}
     * @param {object} p2 - Control point 2 {x, y}
     * @param {object} p3 - End point {x, y}
     * @returns {object} Tangent vector {x, y}
     */
    bezierTangent(t, p0, p1, p2, p3) {
        const t2 = t * t;
        const mt = 1 - t;
        const mt2 = mt * mt;
        
        return {
            x: 3 * mt2 * (p1.x - p0.x) + 6 * mt * t * (p2.x - p1.x) + 3 * t2 * (p3.x - p2.x),
            y: 3 * mt2 * (p1.y - p0.y) + 6 * mt * t * (p2.y - p1.y) + 3 * t2 * (p3.y - p2.y)
        };
    },
    
    /**
     * Calculate angle of bezier tangent at point t
     * @param {number} t - Parameter (0-1)
     * @param {object} p0 - Start point
     * @param {object} p1 - Control point 1
     * @param {object} p2 - Control point 2
     * @param {object} p3 - End point
     * @returns {number} Angle in radians
     */
    bezierAngleAt(t, p0, p1, p2, p3) {
        const tangent = this.bezierTangent(t, p0, p1, p2, p3);
        return Math.atan2(tangent.y, tangent.x);
    },
    
    /**
     * Find nearest point on bezier curve to a given point
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {object} p0 - Start point
     * @param {object} p1 - Control point 1
     * @param {object} p2 - Control point 2
     * @param {object} p3 - End point
     * @param {number} samples - Number of samples (default 50)
     * @returns {object} {t, x, y, distance}
     */
    nearestPointOnBezier(px, py, p0, p1, p2, p3, samples = 50) {
        let minDist = Infinity;
        let minT = 0;
        let minPoint = p0;
        
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            const point = this.pointOnBezier(t, p0, p1, p2, p3);
            const dist = Math.hypot(point.x - px, point.y - py);
            
            if (dist < minDist) {
                minDist = dist;
                minT = t;
                minPoint = point;
            }
        }
        
        return { t: minT, x: minPoint.x, y: minPoint.y, distance: minDist };
    },
    
    /**
     * Calculate bezier curve length (approximate)
     * @param {object} p0 - Start point
     * @param {object} p1 - Control point 1
     * @param {object} p2 - Control point 2
     * @param {object} p3 - End point
     * @param {number} samples - Number of samples
     * @returns {number} Approximate length
     */
    bezierLength(p0, p1, p2, p3, samples = 20) {
        let length = 0;
        let prev = p0;
        
        for (let i = 1; i <= samples; i++) {
            const t = i / samples;
            const point = this.pointOnBezier(t, p0, p1, p2, p3);
            length += Math.hypot(point.x - prev.x, point.y - prev.y);
            prev = point;
        }
        
        return length;
    },
    
    // ========== LINE/SEGMENT OPERATIONS ==========
    
    /**
     * Find nearest point on a line segment to a given point
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {object} lineStart - Line start {x, y}
     * @param {object} lineEnd - Line end {x, y}
     * @returns {object} Nearest point {x, y, t} where t is parameter (0-1)
     */
    nearestPointOnSegment(px, py, lineStart, lineEnd) {
        const A = px - lineStart.x;
        const B = py - lineStart.y;
        const C = lineEnd.x - lineStart.x;
        const D = lineEnd.y - lineStart.y;
        
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let t = lenSq !== 0 ? dot / lenSq : 0;
        
        // Clamp t to [0, 1]
        t = Math.max(0, Math.min(1, t));
        
        return {
            x: lineStart.x + t * C,
            y: lineStart.y + t * D,
            t: t
        };
    },
    
    /**
     * Check if two line segments intersect
     * @param {object} a1 - Segment 1 start {x, y}
     * @param {object} a2 - Segment 1 end {x, y}
     * @param {object} b1 - Segment 2 start {x, y}
     * @param {object} b2 - Segment 2 end {x, y}
     * @returns {object|null} Intersection point {x, y} or null
     */
    lineSegmentIntersection(a1, a2, b1, b2) {
        const d1x = a2.x - a1.x;
        const d1y = a2.y - a1.y;
        const d2x = b2.x - b1.x;
        const d2y = b2.y - b1.y;
        
        const cross = d1x * d2y - d1y * d2x;
        if (Math.abs(cross) < 1e-10) return null; // Parallel
        
        const dx = b1.x - a1.x;
        const dy = b1.y - a1.y;
        
        const t1 = (dx * d2y - dy * d2x) / cross;
        const t2 = (dx * d1y - dy * d1x) / cross;
        
        if (t1 >= 0 && t1 <= 1 && t2 >= 0 && t2 <= 1) {
            return {
                x: a1.x + t1 * d1x,
                y: a1.y + t1 * d1y
            };
        }
        
        return null;
    },
    
    // ========== ANGLE CALCULATIONS ==========
    
    /**
     * Calculate angle between two points
     * @param {object} from - From point {x, y}
     * @param {object} to - To point {x, y}
     * @returns {number} Angle in radians
     */
    angleBetween(from, to) {
        return Math.atan2(to.y - from.y, to.x - from.x);
    },
    
    /**
     * Normalize angle to [-PI, PI]
     * @param {number} angle - Angle in radians
     * @returns {number} Normalized angle
     */
    normalizeAngle(angle) {
        while (angle > Math.PI) angle -= 2 * Math.PI;
        while (angle < -Math.PI) angle += 2 * Math.PI;
        return angle;
    },
    
    /**
     * Convert degrees to radians
     * @param {number} degrees
     * @returns {number} radians
     */
    degToRad(degrees) {
        return degrees * Math.PI / 180;
    },
    
    /**
     * Convert radians to degrees
     * @param {number} radians
     * @returns {number} degrees
     */
    radToDeg(radians) {
        return radians * 180 / Math.PI;
    },
    
    // ========== TRANSFORMATIONS ==========
    
    /**
     * Rotate a point around an origin
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} ox - Origin X
     * @param {number} oy - Origin Y
     * @param {number} angle - Angle in radians
     * @returns {object} Rotated point {x, y}
     */
    rotatePoint(px, py, ox, oy, angle) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        const dx = px - ox;
        const dy = py - oy;
        
        return {
            x: ox + dx * cos - dy * sin,
            y: oy + dx * sin + dy * cos
        };
    },
    
    /**
     * Scale a point from an origin
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {number} ox - Origin X
     * @param {number} oy - Origin Y
     * @param {number} scale - Scale factor
     * @returns {object} Scaled point {x, y}
     */
    scalePoint(px, py, ox, oy, scale) {
        return {
            x: ox + (px - ox) * scale,
            y: oy + (py - oy) * scale
        };
    },
    
    // ========== BOUNDS CALCULATIONS ==========
    
    /**
     * Calculate bounding box for a set of points
     * @param {array} points - Array of {x, y} points
     * @returns {object} {x, y, width, height, left, top, right, bottom}
     */
    getBoundingBox(points) {
        if (!points || points.length === 0) {
            return { x: 0, y: 0, width: 0, height: 0, left: 0, top: 0, right: 0, bottom: 0 };
        }
        
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        for (const p of points) {
            if (p.x < minX) minX = p.x;
            if (p.x > maxX) maxX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.y > maxY) maxY = p.y;
        }
        
        return {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            left: minX,
            top: minY,
            right: maxX,
            bottom: maxY
        };
    },
    
    /**
     * Check if two rectangles overlap
     * @param {object} r1 - First rect {x, y, width, height}
     * @param {object} r2 - Second rect {x, y, width, height}
     * @returns {boolean}
     */
    rectsOverlap(r1, r2) {
        return !(r1.x + r1.width < r2.x || 
                 r2.x + r2.width < r1.x ||
                 r1.y + r1.height < r2.y ||
                 r2.y + r2.height < r1.y);
    },
    
    /**
     * Check if a point is inside a bounding box
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {object} bounds - Bounds {left, top, right, bottom}
     * @returns {boolean}
     */
    isPointInBounds(px, py, bounds) {
        return px >= bounds.left && px <= bounds.right &&
               py >= bounds.top && py <= bounds.bottom;
    },
    
    // ========== POLYGON OPERATIONS ==========
    
    /**
     * Generate regular polygon points
     * @param {number} cx - Center X
     * @param {number} cy - Center Y
     * @param {number} radius - Radius
     * @param {number} sides - Number of sides
     * @param {number} rotation - Rotation offset in radians
     * @returns {array} Array of {x, y} points
     */
    regularPolygon(cx, cy, radius, sides, rotation = 0) {
        const points = [];
        const angleStep = (2 * Math.PI) / sides;
        
        for (let i = 0; i < sides; i++) {
            const angle = rotation + i * angleStep;
            points.push({
                x: cx + radius * Math.cos(angle),
                y: cy + radius * Math.sin(angle)
            });
        }
        
        return points;
    },
    
    /**
     * Check if point is inside polygon (ray casting)
     * @param {number} px - Point X
     * @param {number} py - Point Y
     * @param {array} polygon - Array of {x, y} vertices
     * @returns {boolean}
     */
    isPointInPolygon(px, py, polygon) {
        let inside = false;
        const n = polygon.length;
        
        for (let i = 0, j = n - 1; i < n; j = i++) {
            const xi = polygon[i].x, yi = polygon[i].y;
            const xj = polygon[j].x, yj = polygon[j].y;
            
            if (((yi > py) !== (yj > py)) &&
                (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) {
                inside = !inside;
            }
        }
        
        return inside;
    },
    
    // ========== UTILITY FUNCTIONS ==========
    
    /**
     * Linear interpolation between two values
     * @param {number} a - Start value
     * @param {number} b - End value
     * @param {number} t - Parameter (0-1)
     * @returns {number} Interpolated value
     */
    lerp(a, b, t) {
        return a + (b - a) * t;
    },
    
    /**
     * Linear interpolation between two points
     * @param {object} p1 - Start point {x, y}
     * @param {object} p2 - End point {x, y}
     * @param {number} t - Parameter (0-1)
     * @returns {object} Interpolated point {x, y}
     */
    lerpPoint(p1, p2, t) {
        return {
            x: this.lerp(p1.x, p2.x, t),
            y: this.lerp(p1.y, p2.y, t)
        };
    },
    
    /**
     * Clamp a value between min and max
     * @param {number} value
     * @param {number} min
     * @param {number} max
     * @returns {number}
     */
    clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    },
    
    /**
     * Calculate midpoint between two points
     * @param {object} p1 - First point {x, y}
     * @param {object} p2 - Second point {x, y}
     * @returns {object} Midpoint {x, y}
     */
    midpoint(p1, p2) {
        return {
            x: (p1.x + p2.x) / 2,
            y: (p1.y + p2.y) / 2
        };
    }
};

// Export for use
window.TopologyGeometry = TopologyGeometry;

console.log('TopologyGeometry module loaded');
