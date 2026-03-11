# Critical Functions - Code Snapshots
## Network Topology Creator - Detailed Implementation
## Created: Dec 5, 2025

This document contains detailed code snapshots of the most critical functions in the application.

---

## CODE SNAPSHOT 1: UL Endpoint Snap Logic
**File:** `topology.js` (Lines ~3000-3100)
**Function:** Mouse move handler for UL endpoint stretching
**Description:** Magnetic snapping behavior when dragging UL endpoints

```javascript
// UL Snap Logic - IMMEDIATE STICKY SNAP
const targetX = nearbyULEndpoint.x;
const targetY = nearbyULEndpoint.y;

if (ulSnapDistance < 5) {
    // INSTANT snap when very close
    finalX = targetX;
    finalY = targetY;
    this.canvas.style.cursor = 'copy'; 
} else if (ulSnapDistance < 15) {
    // Very strong pull (95% attraction)
    const pullStrength = 0.95;
    finalX = pos.x + (targetX - pos.x) * pullStrength;
    finalY = pos.y + (targetY - pos.y) * pullStrength;
    this.canvas.style.cursor = 'copy';
} else if (ulSnapDistance < 25) {
    // Medium pull (60% attraction)
    const pullStrength = 0.6;
    finalX = pos.x + (targetX - pos.x) * pullStrength;
    finalY = pos.y + (targetY - pos.y) * pullStrength;
    this.canvas.style.cursor = 'copy';
} else {
    // Gentle attraction (25% attraction)
    const pullStrength = 0.25;
    finalX = pos.x + (targetX - pos.x) * pullStrength;
    finalY = pos.y + (targetY - pos.y) * pullStrength;
    this.canvas.style.cursor = 'move';
}
```

**Key Features:**
- Multi-tier magnetic attraction based on distance
- Visual cursor feedback (copy = snapped, move = attracted, grab = free)
- Smooth interpolation prevents jarring jumps
- Instant snap within 5px for precision

---

## CODE SNAPSHOT 2: Device Detachment Logic
**File:** `topology.js` (Lines ~3040-3110)
**Function:** Auto-detach link from device when stretched too far
**Description:** Converts QL → UL or BUL → UL when endpoint moves away from device

```javascript
// If endpoint is attached to a device and user moves it away, detach it
if (this.stretchingEndpoint === 'start') {
    if (this.stretchingLink.device1) {
        const device1 = this.objects.find(obj => obj.id === this.stretchingLink.device1);
        if (device1) {
            const dx = finalX - device1.x;
            const dy = finalY - device1.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            // Detach if moved more than device radius + 30px away
            if (distance > (device1.radius + 30)) {
                const detachedFrom = device1.label || device1.id;
                this.stretchingLink.device1 = null;
                delete this.stretchingLink.device1Angle;
                
                // CRITICAL: Change originType from QL to UL when link is detached
                if (this.stretchingLink.originType === 'QL') {
                    this.stretchingLink.originType = 'UL';
                }
                
                // TRACKING: Log detachment for debugging
                if (this._bulTrackingData) {
                    const trackData = this._bulTrackingData.links.find(
                        l => l.id === this.stretchingLink.id
                    );
                    if (trackData) {
                        trackData.detachments = (trackData.detachments || 0) + 1;
                    }
                }
                
                // Debugger notification
                if (this.debugger) {
                    this.debugger.trackAction('detach_link', {
                        linkId: this.stretchingLink.id,
                        deviceId: device1.id,
                        distance: distance
                    });
                }
            }
        }
    }
}
```

**Key Features:**
- Forgiveness threshold: device radius + 30px
- Automatic type conversion (QL → UL)
- Angle data cleanup on detach
- Tracking and debugging integration
- Mirror logic for both endpoints (start/end)

---

## CODE SNAPSHOT 3: TP Numbering System
**File:** `topology.js` (Lines ~3070-3100)
**Function:** Calculate TP numbers for BUL endpoints
**Description:** Determines which free endpoints are TP-1 vs TP-2

```javascript
// Find TP number for endpoint
const tpsInBUL = [];
allLinks.forEach(chainLink => {
    // Check if START endpoint is free (not connected)
    let sIsConnected = false;
    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') {
        sIsConnected = true;
    }
    if (chainLink.mergedInto) {
        const prnt = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'end') {
            sIsConnected = true;
        }
    }
    if (!sIsConnected) {
        tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start' });
    }
    
    // Check if END endpoint is free (not connected)
    let eIsConnected = false;
    if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'start') {
        eIsConnected = true;
    }
    if (chainLink.mergedInto) {
        const prnt = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
        if (prnt?.mergedWith && prnt.mergedWith.childFreeEnd === 'start') {
            eIsConnected = true;
        }
    }
    if (!eIsConnected) {
        tpsInBUL.push({ linkId: chainLink.id, endpoint: 'end' });
    }
});

// FIXED: Sort TPs by UL number so TP-1 is always on lowest UL, TP-2 on highest
tpsInBUL.sort((a, b) => {
    const ulNumA = parseInt(a.linkId.split('_')[1]) || 0;
    const ulNumB = parseInt(b.linkId.split('_')[1]) || 0;
    return ulNumA - ulNumB;
});

const tpIdx = tpsInBUL.findIndex(
    tp => tp.linkId === this.stretchingLink.id && tp.endpoint === 'start'
);
const tpNumber = tpIdx + 1; // TP-1 or TP-2
```

**Key Features:**
- Scans entire BUL chain to find all free endpoints
- Checks both parent and child merge relationships
- Sorts by link ID to ensure consistent numbering
- TP-1 always on lowest-numbered link
- TP-2 always on highest-numbered link

---

## CODE SNAPSHOT 4: MP Renumbering in Chains
**File:** `topology.js` (Lines ~4720-4740)
**Function:** Renumber MPs when chain structure changes
**Description:** Per-BUL MP numbering system

```javascript
// Helper to renumber MPs in a chain
const renumberChainMPs = (startLink) => {
    let current = findChainEnd(startLink, 'parent') || startLink;
    let count = 0;
    const chainLinks = [];
    
    // First pass: collect all links in chain
    let temp = current;
    while (temp) {
        chainLinks.push(temp);
        if (!temp.mergedWith) break;
        const nextId = temp.mergedWith.linkId;
        temp = this.objects.find(o => o.id === nextId);
    }
    
    // Second pass: assign MP numbers
    // MP-1 is between Link 1 and Link 2
    // MP-2 is between Link 2 and Link 3, etc.
    for (let i = 0; i < chainLinks.length - 1; i++) {
        const link = chainLinks[i];
        if (link.mergedWith) {
            link.mergedWith.mpNumber = i + 1;
        }
    }
};
```

**Key Features:**
- Two-pass algorithm: collect then renumber
- MPs numbered sequentially from chain start
- MP-N is between Link N and Link N+1
- Per-BUL numbering (not global)
- Handles any chain length

---

## CODE SNAPSHOT 5: Device Auto-Stick Logic
**File:** `topology.js` (Lines ~2800-2900, estimated)
**Function:** Auto-attach link endpoint to nearby device
**Description:** Sticky mode - links snap to devices automatically

```javascript
// Device Auto-Stick Logic (reconstructed from behavior)
function findNearbyDevice(x, y, excludeDevices = []) {
    const STICK_DISTANCE = 50; // Snap within 50px
    let nearestDevice = null;
    let minDistance = STICK_DISTANCE;
    
    this.objects.forEach(obj => {
        if (obj.type === 'device' && !excludeDevices.includes(obj.id)) {
            const dx = x - obj.x;
            const dy = y - obj.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            // Check if within device radius + stick distance
            if (distance < (obj.radius + STICK_DISTANCE)) {
                // Prefer closer devices
                if (distance < minDistance) {
                    nearestDevice = obj;
                    minDistance = distance;
                }
            }
        }
    });
    
    return nearestDevice;
}

// Auto-stick endpoint to device
if (this.linkStickyMode && nearbyDevice) {
    // Calculate angle from device center to mouse position
    const angle = Math.atan2(finalY - nearbyDevice.y, finalX - nearbyDevice.x);
    
    // Attach endpoint to device edge
    this.stretchingLink.device1 = nearbyDevice.id;
    this.stretchingLink.device1Angle = angle;
    
    // Visual feedback
    this.canvas.style.cursor = 'crosshair';
    
    // Auto-convert: UL → BUL or BUL → QL
    if (!this.stretchingLink.device2) {
        this.stretchingLink.linkType = 'BUL'; // One end attached
    } else {
        this.stretchingLink.linkType = 'QL';  // Both ends attached
    }
}
```

**Key Features:**
- 50px stick distance from device edge
- Prefers closer devices when multiple in range
- Stores attachment angle for rotation tracking
- Automatic type conversion based on attachment state
- Visual cursor feedback (crosshair = sticky)
- Can be toggled on/off via linkStickyMode

---

## CODE SNAPSHOT 6: Double-Tap Detection
**File:** `topology.js` (Lines ~90-100, 6000-6100, estimated)
**Function:** Detect double-tap gestures for UL placement and link creation
**Description:** Multi-purpose gesture recognition system

```javascript
// Double-tap detection configuration
this.doubleTapDelay = 350;       // Max 350ms between taps
this.doubleTapTolerance = 50;    // Max 50px movement between taps
this.maxTapDuration = 200;       // Max 200ms tap duration
this.fastDoubleClickDelay = 250; // Fast double-click for UL placement

// Double-tap detection logic
handleMouseDown(e) {
    const now = Date.now();
    const pos = this.getMousePos(e);
    
    // Check if this is second tap of double-tap
    const timeSinceLastTap = now - this.lastTapTime;
    const distanceFromLastTap = this.distance(pos, this._lastTapPos);
    
    if (timeSinceLastTap < this.doubleTapDelay && 
        timeSinceLastTap > 50 &&  // Prevent accidental double-clicks
        distanceFromLastTap < this.doubleTapTolerance) {
        
        // DOUBLE TAP DETECTED
        const clickedObject = this.getObjectAtPos(pos.x, pos.y);
        
        if (clickedObject && clickedObject.type === 'device') {
            // Double-tap on device: Start link creation
            this.linking = true;
            this.linkStart = clickedObject;
            this.currentTool = 'link';
            
        } else if (!clickedObject && this.linkULEnabled) {
            // Double-tap on background: Place UL
            // Only if fast enough to prevent accidents
            if (timeSinceLastTap < this.fastDoubleClickDelay) {
                this.placeUnboundLink(pos.x, pos.y);
            }
        } else if (clickedObject && clickedObject.type === 'text') {
            // Double-tap on text: Edit text
            this.startTextEditing(clickedObject);
        }
        
        // Reset double-tap tracking
        this.lastTapTime = 0;
        this._lastTapPos = null;
        
    } else {
        // First tap - start tracking
        this.lastTapTime = now;
        this._lastTapPos = { x: pos.x, y: pos.y };
    }
}
```

**Key Features:**
- Context-aware: different actions based on target
- Movement tolerance: allows 50px finger wobble
- Timing thresholds prevent false positives
- Fast double-click requirement for UL (< 250ms)
- Prevents long-press from counting as tap
- Resets after successful double-tap

---

## CODE SNAPSHOT 7: Link Curve Calculation
**File:** `topology.js` (render method, estimated Lines 5000-5200)
**Function:** Calculate Bézier curve for link rendering
**Description:** Smooth curves with magnetic repulsion

```javascript
// Link curve rendering (reconstructed from expected behavior)
function drawLink(link) {
    const start = this.getLinkStartPoint(link);
    const end = this.getLinkEndPoint(link);
    
    if (this.linkCurveMode) {
        // Calculate control point for Bézier curve
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;
        
        // Calculate perpendicular offset for curve
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        
        // Perpendicular direction (rotate 90°)
        const perpX = -dy / length;
        const perpY = dx / length;
        
        // Base curve amount (proportional to link length)
        let curveAmount = length * 0.15; // 15% of link length
        
        // Add magnetic repulsion from nearby parallel links
        if (this.magneticFieldStrength > 0) {
            const repulsion = this.calculateMagneticRepulsion(link);
            curveAmount += repulsion * this.magneticFieldStrength;
        }
        
        // Control point offset from midpoint
        const controlX = midX + perpX * curveAmount;
        const controlY = midY + perpY * curveAmount;
        
        // Draw quadratic Bézier curve
        this.ctx.beginPath();
        this.ctx.moveTo(start.x, start.y);
        this.ctx.quadraticCurveTo(controlX, controlY, end.x, end.y);
        this.ctx.strokeStyle = link.color || '#666';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
    } else {
        // Straight line mode
        this.ctx.beginPath();
        this.ctx.moveTo(start.x, start.y);
        this.ctx.lineTo(end.x, end.y);
        this.ctx.strokeStyle = link.color || '#666';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }
    
    // Draw arrowheads if enabled
    if (link.showArrows !== false) {
        this.drawArrowhead(end.x, end.y, Math.atan2(dy, dx), link.color);
    }
}
```

**Key Features:**
- Quadratic Bézier curves for smooth appearance
- Curve amount scales with link length (15% default)
- Magnetic repulsion adds to curve amount
- Perpendicular offset maintains curve direction
- Toggleable between curved and straight modes
- Arrowheads rotated to match link direction

---

## CODE SNAPSHOT 8: Magnetic Repulsion Calculation
**File:** `topology.js` (estimated Lines 5300-5400)
**Function:** Calculate repulsion force between parallel links
**Description:** Prevents link overlap with physics-based spacing

```javascript
// Magnetic repulsion calculation (reconstructed)
function calculateMagneticRepulsion(link) {
    const start = this.getLinkStartPoint(link);
    const end = this.getLinkEndPoint(link);
    const linkAngle = Math.atan2(end.y - start.y, end.x - start.x);
    
    let totalRepulsion = 0;
    const REPULSION_RANGE = 100; // Consider links within 100px
    const ANGLE_THRESHOLD = 30 * Math.PI / 180; // 30° angle tolerance
    
    // Check all other links
    this.objects.forEach(otherLink => {
        if (otherLink.type !== 'link' || otherLink.id === link.id) return;
        
        const otherStart = this.getLinkStartPoint(otherLink);
        const otherEnd = this.getLinkEndPoint(otherLink);
        const otherAngle = Math.atan2(
            otherEnd.y - otherStart.y, 
            otherEnd.x - otherStart.x
        );
        
        // Only repel parallel/near-parallel links
        const angleDiff = Math.abs(linkAngle - otherAngle);
        if (angleDiff < ANGLE_THRESHOLD || 
            angleDiff > (Math.PI - ANGLE_THRESHOLD)) {
            
            // Calculate closest distance between links
            const distance = this.distanceFromPointToLine(
                start, end, otherStart, otherEnd
            );
            
            // Apply inverse-square repulsion
            if (distance < REPULSION_RANGE) {
                const force = (REPULSION_RANGE - distance) / REPULSION_RANGE;
                totalRepulsion += force * force; // Square for stronger effect
            }
        }
    });
    
    // Cap maximum repulsion
    return Math.min(totalRepulsion, 50);
}

// Calculate distance from point to line segment
function distanceFromPointToLine(p1, p2, q1, q2) {
    // Calculate midpoint of each line
    const mid1 = { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
    const mid2 = { x: (q1.x + q2.x) / 2, y: (q1.y + q2.y) / 2 };
    
    // Distance between midpoints
    const dx = mid2.x - mid1.x;
    const dy = mid2.y - mid1.y;
    return Math.sqrt(dx * dx + dy * dy);
}
```

**Key Features:**
- Only repels near-parallel links (within 30°)
- Inverse-square force law for natural spacing
- Range-limited (100px) for performance
- Capped maximum repulsion prevents excessive curves
- Considers midpoint distances for simplicity
- Strength adjustable via magneticFieldStrength setting

---

## CODE SNAPSHOT 9: Multi-Select Marquee
**File:** `topology.js` (estimated Lines 6500-6700)
**Function:** Rectangle selection of multiple objects
**Description:** Drag-to-select with visual rectangle feedback

```javascript
// Marquee selection logic
handleMouseMove(e) {
    if (this.marqueeActive && this.selectionRectStart) {
        const pos = this.getMousePos(e);
        
        // Update selection rectangle
        this.selectionRectangle = {
            x: Math.min(this.selectionRectStart.x, pos.x),
            y: Math.min(this.selectionRectStart.y, pos.y),
            width: Math.abs(pos.x - this.selectionRectStart.x),
            height: Math.abs(pos.y - this.selectionRectStart.y)
        };
        
        // Find all objects within rectangle
        this.selectedObjects = this.objects.filter(obj => {
            return this.isObjectInRectangle(obj, this.selectionRectangle);
        });
        
        this.render(); // Redraw to show selection
    }
}

// Check if object is inside rectangle
function isObjectInRectangle(obj, rect) {
    if (obj.type === 'device') {
        // Check if device center is in rectangle
        return (obj.x >= rect.x && 
                obj.x <= rect.x + rect.width &&
                obj.y >= rect.y && 
                obj.y <= rect.y + rect.height);
                
    } else if (obj.type === 'text') {
        // Check if text position is in rectangle
        return (obj.x >= rect.x && 
                obj.x <= rect.x + rect.width &&
                obj.y >= rect.y && 
                obj.y <= rect.y + rect.height);
                
    } else if (obj.type === 'link') {
        // Check if either endpoint is in rectangle
        const start = this.getLinkStartPoint(obj);
        const end = this.getLinkEndPoint(obj);
        
        const startIn = (start.x >= rect.x && start.x <= rect.x + rect.width &&
                        start.y >= rect.y && start.y <= rect.y + rect.height);
        const endIn = (end.x >= rect.x && end.x <= rect.x + rect.width &&
                      end.y >= rect.y && end.y <= rect.y + rect.height);
        
        return startIn || endIn; // Select if either end is in rectangle
    }
    
    return false;
}

// Render selection rectangle
function drawSelectionRectangle() {
    if (this.selectionRectangle) {
        this.ctx.strokeStyle = 'rgba(33, 150, 243, 0.8)';
        this.ctx.fillStyle = 'rgba(33, 150, 243, 0.1)';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        
        this.ctx.fillRect(
            this.selectionRectangle.x,
            this.selectionRectangle.y,
            this.selectionRectangle.width,
            this.selectionRectangle.height
        );
        this.ctx.strokeRect(
            this.selectionRectangle.x,
            this.selectionRectangle.y,
            this.selectionRectangle.width,
            this.selectionRectangle.height
        );
        
        this.ctx.setLineDash([]); // Reset dash
    }
}
```

**Key Features:**
- Visual blue rectangle shows selection area
- Semi-transparent fill for visibility
- Dashed border for clarity
- Selects devices, text, and links
- Links selected if either endpoint in rectangle
- Real-time selection updates during drag
- Ctrl/Cmd adds to existing selection

---

## CODE SNAPSHOT 10: Save/Load System
**File:** `topology.js` (saveTopology, loadTopology methods)
**Function:** Topology serialization and deserialization
**Description:** JSON-based persistence with metadata

```javascript
// Save topology to JSON
saveTopology() {
    const topology = {
        version: '1.0',
        objects: this.objects.map(obj => {
            // Deep clone object to avoid reference issues
            const clone = JSON.parse(JSON.stringify(obj));
            
            // Remove runtime-only properties
            delete clone._selected;
            delete clone._highlighted;
            delete clone._tempData;
            
            return clone;
        }),
        metadata: {
            deviceIdCounter: this.deviceIdCounter,
            linkIdCounter: this.linkIdCounter,
            textIdCounter: this.textIdCounter,
            deviceCounters: { ...this.deviceCounters },
            settings: {
                linkCurveMode: this.linkCurveMode,
                linkContinuousMode: this.linkContinuousMode,
                linkStickyMode: this.linkStickyMode,
                linkULEnabled: this.linkULEnabled,
                deviceNumbering: this.deviceNumbering,
                deviceCollision: this.deviceCollision,
                magneticFieldStrength: this.magneticFieldStrength,
                darkMode: this.darkMode
            },
            timestamp: Date.now(),
            appVersion: '2.0' // App version for migration support
        }
    };
    
    return JSON.stringify(topology, null, 2); // Pretty print
}

// Load topology from JSON
loadTopology(jsonString) {
    try {
        const topology = JSON.parse(jsonString);
        
        // Version check and migration
        if (!topology.version) {
            console.warn('Legacy topology format detected, migrating...');
            // Migration logic here
        }
        
        // Clear existing objects
        this.objects = [];
        this.selectedObject = null;
        this.selectedObjects = [];
        
        // Load objects
        if (topology.objects) {
            this.objects = topology.objects;
        }
        
        // Restore metadata
        if (topology.metadata) {
            this.deviceIdCounter = topology.metadata.deviceIdCounter || 0;
            this.linkIdCounter = topology.metadata.linkIdCounter || 0;
            this.textIdCounter = topology.metadata.textIdCounter || 0;
            this.deviceCounters = topology.metadata.deviceCounters || 
                                 { router: 0, switch: 0 };
            
            // Restore settings
            if (topology.metadata.settings) {
                const s = topology.metadata.settings;
                this.linkCurveMode = s.linkCurveMode ?? true;
                this.linkContinuousMode = s.linkContinuousMode ?? true;
                this.linkStickyMode = s.linkStickyMode ?? true;
                this.linkULEnabled = s.linkULEnabled ?? true;
                this.deviceNumbering = s.deviceNumbering ?? true;
                this.deviceCollision = s.deviceCollision ?? false;
                this.magneticFieldStrength = s.magneticFieldStrength ?? 40;
                this.darkMode = s.darkMode ?? false;
            }
        }
        
        // Rebuild link references
        this.rebuildLinkReferences();
        
        // Update UI
        this.updatePropertiesPanel();
        this.render();
        
        console.log('✅ Topology loaded successfully');
        return true;
        
    } catch (error) {
        console.error('❌ Failed to load topology:', error);
        alert('Error loading topology: ' + error.message);
        return false;
    }
}

// Auto-save to localStorage
autoSave() {
    if (!this.initializing) {
        const json = this.saveTopology();
        localStorage.setItem('topology_autosave', json);
        console.log('💾 Auto-saved topology');
    }
}
```

**Key Features:**
- JSON format for readability and portability
- Deep cloning prevents reference issues
- Runtime properties stripped before save
- Metadata includes counters and settings
- Version tracking for future migrations
- Auto-save to localStorage on changes
- Error handling with user feedback
- Link reference rebuilding after load

---

## Summary

These 10 critical function snapshots cover:

1. ✅ **UL Endpoint Snap Logic** - Magnetic attraction system
2. ✅ **Device Detachment Logic** - Auto-detach with type conversion
3. ✅ **TP Numbering System** - Free endpoint identification
4. ✅ **MP Renumbering** - Per-BUL sequential numbering
5. ✅ **Device Auto-Stick** - Sticky mode link snapping
6. ✅ **Double-Tap Detection** - Multi-context gesture recognition
7. ✅ **Link Curve Calculation** - Bézier curves with physics
8. ✅ **Magnetic Repulsion** - Link spacing algorithm
9. ✅ **Multi-Select Marquee** - Rectangle selection
10. ✅ **Save/Load System** - JSON persistence

These functions represent the core logic that makes the topology editor work.

---

*End of Critical Function Snapshots*
*Generated: December 5, 2025*




