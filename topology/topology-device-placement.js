/**
 * topology-device-placement.js - Device Placement and Collision Detection
 * 
 * Extracted from topology.js for modular architecture.
 * Contains collision detection logic for device placement and movement.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.DevicePlacement = {

    /**
     * Get collision radius in a specific direction (angle in radians)
     * This gives the EXACT distance from center to edge in that direction
     */
    getCollisionRadiusInDirection(editor, device, angle) {
        const bounds = editor.getDeviceVisualBounds(device);
        const rotation = bounds.rotation || 0;
        const localAngle = angle - rotation;
        
        switch (bounds.type) {
            case 'circle':
                return bounds.radius;
                
            case 'rectangle': {
                const hw = bounds.width / 2;
                const hh = bounds.height / 2;
                const cosA = Math.cos(localAngle);
                const sinA = Math.sin(localAngle);
                const absCosA = Math.abs(cosA);
                const absSinA = Math.abs(sinA);
                
                if (absCosA < 0.001) return hh;
                if (absSinA < 0.001) return hw;
                
                const tx = hw / absCosA;
                const ty = hh / absSinA;
                return Math.min(tx, ty);
            }
            
            case 'server': {
                const cosA = Math.cos(localAngle);
                const sinA = Math.sin(localAngle);
                const absCosA = Math.abs(cosA);
                const absSinA = Math.abs(sinA);
                
                const hx = cosA >= 0 ? bounds.rightExtent : bounds.leftExtent;
                const hy = sinA >= 0 ? bounds.bottomExtent : bounds.topExtent;
                
                if (absCosA < 0.001) return hy;
                if (absSinA < 0.001) return hx;
                
                const tx = hx / absCosA;
                const ty = hy / absSinA;
                return Math.min(tx, ty);
            }
                
            case 'hexagon': {
                const hexR = bounds.hexRadius;
                let a = localAngle % (2 * Math.PI);
                if (a < 0) a += 2 * Math.PI;
                
                const sectorAngle = a % (Math.PI / 3);
                const angleFromSectorCenter = Math.abs(sectorAngle - Math.PI / 6);
                const distRatio = Math.cos(Math.PI / 6) / Math.cos(angleFromSectorCenter);
                return hexR * Math.min(distRatio, 1.0);
            }
                
            case 'ellipse': {
                const a = bounds.width / 2;
                const b = bounds.height / 2;
                const cosA = Math.cos(localAngle);
                const sinA = Math.sin(localAngle);
                return (a * b) / Math.sqrt((b * cosA) ** 2 + (a * sinA) ** 2);
            }
                
            default:
                return device.radius || 30;
        }
    },

    /**
     * Get collision radius using bounding circle (legacy, for when direction doesn't matter)
     */
    getCollisionRadius(editor, device) {
        const bounds = editor.getDeviceVisualBounds(device);
        switch (bounds.type) {
            case 'circle':
                return bounds.radius;
            case 'rectangle':
                return Math.sqrt((bounds.width/2)**2 + (bounds.height/2)**2);
            case 'server':
                const maxHx = Math.max(bounds.leftExtent, bounds.rightExtent);
                const maxHy = Math.max(bounds.topExtent, bounds.bottomExtent);
                return Math.sqrt(maxHx**2 + maxHy**2);
            case 'hexagon':
                return bounds.hexRadius;
            case 'ellipse':
                return Math.sqrt((bounds.width/2)**2 + (bounds.height/2)**2);
            default:
                return device.radius || 30;
        }
    },

    /**
     * Check and resolve device collision
     */
    checkCollision(editor, movingDevice, proposedX, proposedY) {
        // Don't apply collision if device is being locked for grab setup
        if (editor._lockingDeviceForGrab && editor._lockedDevice === movingDevice) {
            return { x: proposedX, y: proposedY };
        }
        
        // Get list of ALL devices that are currently being dragged
        const movingDevices = new Set();
        movingDevices.add(movingDevice.id);
        
        if (editor.selectedObjects && editor.selectedObjects.length > 1 && editor.multiSelectInitialPositions) {
            editor.selectedObjects.forEach(obj => {
                if (obj.type === 'device' && obj.id !== movingDevice.id) {
                    movingDevices.add(obj.id);
                }
            });
        }
        
        const otherDevices = editor.objects.filter(obj => 
            obj.type === 'device' && !movingDevices.has(obj.id) && 
            !(editor._lockingDeviceForGrab && editor._lockedDevice === obj)
        );
        
        let x = proposedX;
        let y = proposedY;
        const maxIterations = 8;
        const epsilon = 0.01;
        let collisionDetected = false;
        const collisionSet = new Set();
        
        for (let iter = 0; iter < maxIterations; iter++) {
            let adjusted = false;
            for (const obj of otherDevices) {
                const dx = x - obj.x;
                const dy = y - obj.y;
                let dist = Math.sqrt(dx * dx + dy * dy);
                
                let nx, ny, angle;
                if (dist < epsilon) {
                    nx = 1; ny = 0; dist = epsilon;
                    angle = 0;
                } else {
                    nx = dx / dist; 
                    ny = dy / dist;
                    angle = Math.atan2(dy, dx);
                }
                
                const movingRadiusDir = this.getCollisionRadiusInDirection(editor, movingDevice, angle);
                const objRadiusDir = this.getCollisionRadiusInDirection(editor, obj, angle + Math.PI);
                const minDist = movingRadiusDir + objRadiusDir + 1;
                
                if (dist < minDist) {
                    const push = minDist - dist;
                    x += nx * push;
                    y += ny * push;
                    adjusted = true;
                    collisionDetected = true;
                    collisionSet.add(obj.label || obj.id);
                }
            }
            if (!adjusted) break;
        }
        
        // Throttled logging
        const now = Date.now();
        if (editor.debugger && collisionDetected) {
            if (!editor._lastCollisionLog || now - editor._lastCollisionLog > 500) {
                editor._lastCollisionLog = now;
                const movingLabel = movingDevice.label || 'Device';
                const uniqueCollisions = Array.from(collisionSet);
                const summary = uniqueCollisions.length > 3 
                    ? `${uniqueCollisions.slice(0, 3).join(', ')} +${uniqueCollisions.length - 3} more`
                    : uniqueCollisions.join(', ');
                editor.debugger.logWarning(`Collision: ${movingLabel} vs ${summary}`);
            }
        }
        
        return { x, y };
    }
};

console.log('[topology-device-placement.js] DevicePlacement loaded');
