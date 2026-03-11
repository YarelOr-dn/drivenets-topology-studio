# BUL Movement from Any UL Body + Device Sync to Link Table

## Overview
Implemented two key enhancements:
1. **BUL can now be dragged from ANY UL body in the chain** (not just the first link)
2. **Endpoint devices sync to link details table** with TP-1/TP-2 labels

---

## Feature 1: Drag BUL from Any UL Body ✅

### Problem
Previously, dragging different ULs in a BUL chain might not work consistently. Movement logic only worked reliably for the first or selected link.

### Solution

#### A. Store Initial Positions for ALL Links (Lines 1986-2012)

**Enhanced the grab logic** to store initial positions for the entire BUL chain:

```javascript
// ✨ ENHANCED: Store initial positions for ALL links in BUL chain
// This allows dragging from ANY UL body in the chain
if (clickedObject.mergedWith || clickedObject.mergedInto) {
    const allChainLinks = this.getAllMergedLinks(clickedObject);
    this._bulChainInitialPositions = new Map();
    
    allChainLinks.forEach(chainLink => {
        this._bulChainInitialPositions.set(chainLink.id, {
            startX: chainLink.start.x,
            startY: chainLink.start.y,
            endX: chainLink.end.x,
            endY: chainLink.end.y
        });
    });
    
    if (this.debugger) {
        this.debugger.logInfo(`📦 Stored initial positions for ${allChainLinks.length} links in BUL`);
    }
}
```

**Location**: `handleMouseDown()` when clicking on unbound link body

**Benefits**:
- ✅ Captures initial state of ALL links in the chain
- ✅ Uses a Map for efficient lookup by link ID
- ✅ Works regardless of which link you click

---

#### B. Move ALL Links as Rigid Unit (Lines 3793-3820)

**Completely rewrote the movement logic** for cleaner, more reliable behavior:

```javascript
// ✨ ENHANCED: Move ENTIRE BUL chain as one rigid unit (from ANY UL body!)
// Uses stored initial positions for ALL links to move them together smoothly

if (this._bulChainInitialPositions && this._bulChainInitialPositions.size > 0) {
    // Move ALL links in the BUL chain by the same delta
    this._bulChainInitialPositions.forEach((initialPos, linkId) => {
        const chainLink = this.objects.find(o => o.id === linkId);
        if (chainLink) {
            chainLink.start.x = initialPos.startX + dx;
            chainLink.start.y = initialPos.startY + dy;
            chainLink.end.x = initialPos.endX + dx;
            chainLink.end.y = initialPos.endY + dy;
        }
    });
    
    // Update all connection points (MPs) to match new positions
    this.updateAllConnectionPoints();
    
    if (this.debugger && !this._unboundBodyDragLogged) {
        this._unboundBodyDragLogged = true;
        const chainSize = this._bulChainInitialPositions.size;
        this.debugger.logSuccess(`↔️ BUL Chain moved: All ${chainSize} ULs moved as rigid unit`);
        this.debugger.logInfo(`   ✨ Can drag from ANY UL body in the chain!`);
    }
}
```

**Location**: `handleMouseMove()` during unbound link body dragging

**How It Works**:
1. Calculates total drag delta (`dx`, `dy`) from initial mouse position
2. Applies same delta to ALL links in the chain using stored initial positions
3. Updates all MP (connection point) metadata to match
4. Entire BUL moves as one rigid, connected unit

**Key Improvements**:
- ✅ **Simple and reliable** - all links moved by same delta
- ✅ **No propagation errors** - no recursive calculation issues
- ✅ **Works from any link** - head, middle, or tail
- ✅ **Maintains connections** - MPs stay perfectly aligned
- ✅ **No jumps or jitter** - smooth movement

---

### Visual Result

**Before**: 
```
Could only drag reliably from first link
Middle links might not move entire chain
```

**After**:
```
Click ANY UL body in the BUL:
  ○━━━━●━━━━○━━━━●
   UL1   UL2   UL3
    ↕     ↕     ↕
  ALL move together as rigid unit!
```

---

## Feature 2: Endpoint Devices Sync to Link Table ✅

### Problem
The link details table didn't clearly show which devices were at BUL endpoints (TP-1 and TP-2). It might show random devices from the chain or be confusing.

### Solution

#### A. Enhanced getAllConnectedDevices() (Lines 7493-7578)

**Added TP endpoint device tracking**:

```javascript
// ENHANCED: For BULs, identify which devices are at the FREE TPs (endpoints)
let tp1Device = null;
let tp2Device = null;

if (allMergedLinks.length > 1) {
    // This is a BUL - find the TP-1 and TP-2 endpoint devices
    const tpsInBUL = [];
    
    for (const chainLink of allMergedLinks) {
        // Check if start is a free TP
        let startIsConnected = false;
        if (chainLink.mergedWith && chainLink.mergedWith.parentFreeEnd === 'end') startIsConnected = true;
        if (chainLink.mergedInto) {
            const parent = this.objects.find(o => o.id === chainLink.mergedInto.parentId);
            if (parent?.mergedWith && parent.mergedWith.childFreeEnd === 'end') startIsConnected = true;
        }
        if (!startIsConnected) {
            tpsInBUL.push({ linkId: chainLink.id, endpoint: 'start', link: chainLink });
        }
        
        // [Same for end endpoint...]
    }
    
    // Sort TPs by link ID (BUL rule: lower ID = TP-1)
    tpsInBUL.sort((a, b) => {
        const idNumA = parseInt(a.linkId.split('_')[1]) || 0;
        const idNumB = parseInt(b.linkId.split('_')[1]) || 0;
        if (idNumA === idNumB) return a.endpoint === 'start' ? -1 : 1;
        return idNumA - idNumB;
    });
    
    // Get devices at TP-1 and TP-2
    if (tpsInBUL.length >= 1) {
        const tp1 = tpsInBUL[0];
        const tp1DeviceId = tp1.endpoint === 'start' ? tp1.link.device1 : tp1.link.device2;
        if (tp1DeviceId) {
            tp1Device = this.objects.find(obj => obj.id === tp1DeviceId);
        }
    }
    if (tpsInBUL.length >= 2) {
        const tp2 = tpsInBUL[1];
        const tp2DeviceId = tp2.endpoint === 'start' ? tp2.link.device1 : tp2.link.device2;
        if (tp2DeviceId) {
            tp2Device = this.objects.find(obj => obj.id === tp2DeviceId);
        }
    }
}

return {
    deviceIds: Array.from(deviceIds),
    devices: deviceObjects,
    count: deviceIds.size,
    links: allMergedLinks,
    // ENHANCED: Endpoint devices for BULs
    tp1Device: tp1Device,  // Device at TP-1 (lower-ID link's free TP)
    tp2Device: tp2Device   // Device at TP-2 (higher-ID link's free TP)
};
```

**What This Does**:
1. Finds all free TPs in the BUL
2. Sorts them by BUL rule (lower ID = TP-1)
3. Identifies which device is attached to TP-1
4. Identifies which device is attached to TP-2
5. Returns this info in the result object

---

#### B. Use Endpoint Devices in Link Table (Lines 9259-9297)

**Enhanced device selection for table display**:

```javascript
// ENHANCED: For BULs, show devices at TP-1 and TP-2 (endpoint devices only)
const isBUL = link.mergedWith || link.mergedInto;

if (isBUL && (connectedDevicesInfo.tp1Device || connectedDevicesInfo.tp2Device)) {
    // BUL with endpoint devices - show TP-1 and TP-2 devices specifically
    device1 = connectedDevicesInfo.tp1Device;
    device2 = connectedDevicesInfo.tp2Device;
    
    const linkCount = connectedDevicesInfo.links.length;
    const deviceInfo = connectedDevicesInfo.tp1Device && connectedDevicesInfo.tp2Device ? '2 endpoint devices' :
                      connectedDevicesInfo.tp1Device || connectedDevicesInfo.tp2Device ? '1 endpoint device' : 'no endpoint devices';
    
    linkInfo = `<strong style="color: #9b59b6;">🔗 BUL CHAIN:</strong> ${linkCount} link(s), ${deviceInfo}`;
    
    if (this.debugger) {
        this.debugger.logInfo(`📊 Link Table: BUL with ${linkCount} links`);
        if (device1) this.debugger.logInfo(`   TP-1 Device: ${device1.label || device1.id}`);
        if (device2) this.debugger.logInfo(`   TP-2 Device: ${device2.label || device2.id}`);
    }
}
```

**Benefits**:
- ✅ Shows the CORRECT devices (at endpoints, not random)
- ✅ Clear about what "device1" and "device2" mean for BULs
- ✅ Console logging helps verify correct devices shown

---

#### C. Label Devices with TP Numbers (Lines 9344-9359)

**Added TP-1 and TP-2 labels in table**:

```javascript
// ENHANCED: For BULs, show endpoint devices with TP labels
let device1Name, device2Name;
if (isBUL && connectedDevicesInfo.tp1Device) {
    device1Name = `<strong style="color: #9b59b6;">TP-1:</strong> ${connectedDevicesInfo.tp1Device.label || 'Device 1'}`;
} else {
    device1Name = device1 ? (device1.label || 'Device 1') : 'Unbound';
}

if (isBUL && connectedDevicesInfo.tp2Device) {
    device2Name = `<strong style="color: #9b59b6;">TP-2:</strong> ${connectedDevicesInfo.tp2Device.label || 'Device 2'}`;
} else {
    device2Name = device2 ? (device2.label || 'Device 2') : 'Unbound';
}
```

**Visual Result in Table**:
```
┌─────────────┬───────────┬──────┬─────────────┬────┬─────────────┬──────┬───────────┬─────────────┐
│   Device    │ Interface │ VLAN │ Transceiver │ ↔  │ Transceiver │ VLAN │ Interface │   Device    │
├─────────────┼───────────┼──────┼─────────────┼────┼─────────────┼──────┼───────────┼─────────────┤
│ TP-1: NCP-1 │ eth0      │ 100  │ 400G DR4    │ ↔  │ 400G DR4    │ 100  │ eth1      │ TP-2: NCP-2 │
└─────────────┴───────────┴──────┴─────────────┴────┴─────────────┴──────┴───────────┴─────────────┘
       ↑                                                                                      ↑
    Purple "TP-1:" label shows this is BUL TP-1 device               Purple "TP-2:" label
```

---

## How It Works Now

### 1. Dragging BUL from Any UL Body

**User Experience**:
```
Step 1: Create BUL with 3 links
        U3━━━━MP━━━━U5━━━━MP━━━━U7
        
Step 2: Click on ANY UL body (U3, U5, or U7)
        → All 3 links selected (highlighted in blue)
        
Step 3: Drag from clicked link
        → Entire BUL moves as rigid unit
        → All MPs maintain perfect alignment
        → All links stay connected
        
Step 4: Release
        → BUL in new position
        → Structure perfectly preserved
```

**Works From**:
- ✅ Head link (U3) - moves entire chain
- ✅ Middle link (U5) - moves entire chain
- ✅ Tail link (U7) - moves entire chain

---

### 2. Link Table Device Sync

**When you open link details** for a BUL:

**Before**:
```
Device          | ... | Device
NCP-1           | ... | NCP-5
(unclear which is at TP-1 or TP-2)
```

**After**:
```
Device          | ... | Device
TP-1: NCP-1     | ... | TP-2: NCP-5
(crystal clear - shows endpoint devices with TP labels)
```

**Header Shows**:
```
🔗 BUL CHAIN: 3 link(s), 2 endpoint devices
```

---

## Technical Details

### Initial Position Storage

**Data Structure**:
```javascript
this._bulChainInitialPositions = Map {
    'unbound_3' => { startX: 100, startY: 200, endX: 300, endY: 200 },
    'unbound_5' => { startX: 300, startY: 200, endX: 500, endY: 200 },
    'unbound_7' => { startX: 500, startY: 200, endX: 700, endY: 200 }
}
```

**Lifetime**:
- **Created**: When clicking on any UL in a BUL
- **Used**: Every frame during drag to calculate new positions
- **Cleared**: On mouse release (cleanup)

---

### Movement Algorithm

**For each frame during drag**:
```javascript
1. Calculate mouse delta:
   dx = currentMouseX - initialMouseX
   dy = currentMouseY - initialMouseY

2. Apply delta to ALL links:
   for each link in BUL:
       link.start.x = initialStart.x + dx
       link.start.y = initialStart.y + dy
       link.end.x = initialEnd.x + dx
       link.end.y = initialEnd.y + dy

3. Update connection points:
   updateAllConnectionPoints()  // Syncs MP metadata

4. Redraw:
   this.draw()
```

**Result**: All links move by exact same delta - perfect rigid body movement!

---

### Endpoint Device Detection

**Algorithm**:
```javascript
1. Get all links in BUL chain
2. For each link, check if start/end is a free TP
3. Collect all free TPs with their link IDs and endpoints
4. Sort TPs by link ID (BUL rule: lower ID = TP-1)
5. TP-1 = first TP in sorted list
6. TP-2 = second TP in sorted list
7. Get device attached to TP-1 endpoint
8. Get device attached to TP-2 endpoint
9. Return both devices in result
```

**Used By**:
- Link details table (shows in device columns)
- Console logging (debugging output)
- Any code that needs endpoint device info

---

## Console Output Examples

### Dragging BUL from Middle Link
```
🖐️ Unbound link grabbed for body dragging via TRACKPAD
📍 Start: (300.0, 200.0), End: (500.0, 200.0)
📍 Mouse: (400.0, 200.0) - dragStart stores POSITION, not offset
   📦 Stored initial positions for 3 links in BUL

[During drag]
↔️ BUL Chain moved: All 3 ULs moved as rigid unit
   ✨ Can drag from ANY UL body in the chain!
```

### Opening Link Table for BUL
```
📊 Link Table: BUL with 3 links
   TP-1 Device: NCP-1
   TP-2 Device: NCP-5
```

---

## Testing Verification

### Test Case 1: Drag from Head Link
```
Setup:
- BUL: U3--MP--U5--MP--U7
- Devices: NCP-1 at U3-start (TP-1), NCP-5 at U7-end (TP-2)

Action:
1. Click on U3 body (head link)
2. Drag to new position

Expected:
✅ All 3 links selected (highlighted)
✅ Entire BUL moves together
✅ MPs stay perfectly aligned
✅ No separation or jitter
```

### Test Case 2: Drag from Middle Link
```
Setup: Same BUL

Action:
1. Click on U5 body (middle link)
2. Drag to new position

Expected:
✅ All 3 links selected
✅ Entire BUL moves as unit
✅ Can drag from middle - works perfectly!
✅ Structure maintained
```

### Test Case 3: Drag from Tail Link
```
Setup: Same BUL

Action:
1. Click on U7 body (tail link)
2. Drag to new position

Expected:
✅ All 3 links selected
✅ Entire BUL moves together
✅ Tail dragging works same as head
```

### Test Case 4: Link Table Device Sync
```
Setup: Same BUL with devices

Action:
1. Right-click on any link in BUL
2. Select "Link Details"

Expected in table:
┌──────────────┬────┬──────────────┐
│    Device    │ ↔  │    Device    │
├──────────────┼────┼──────────────┤
│ TP-1: NCP-1  │ ↔  │ TP-2: NCP-5  │
└──────────────┴────┴──────────────┘

✅ Shows TP-1 device (at BUL start)
✅ Shows TP-2 device (at BUL end)
✅ Purple "TP-1:" and "TP-2:" labels
✅ Clear which device is which endpoint
```

### Test Case 5: BUL with One Device
```
Setup: BUL with only TP-1 attached to device

Expected:
┌──────────────┬────┬──────────────┐
│    Device    │ ↔  │    Device    │
├──────────────┼────┼──────────────┤
│ TP-1: NCP-1  │ ↔  │   Unbound    │
└──────────────┴────┴──────────────┘

✅ TP-1 device shown correctly
✅ TP-2 shows "Unbound" (no device)
```

---

## Summary of Changes

### Files Modified
- `topology.js`
  - Lines 1986-2012: Store initial positions for all BUL links on grab
  - Lines 3793-3870: Move all BUL links as rigid unit using stored positions
  - Lines 7493-7578: Enhanced getAllConnectedDevices() to identify TP endpoint devices
  - Lines 9259-9297: Use TP endpoint devices in link table display
  - Lines 9344-9359: Add TP-1/TP-2 labels to device names in table

### Key Improvements

1. ✅ **Drag from any UL body** - head, middle, or tail all work
2. ✅ **Rigid body movement** - entire BUL moves as one unit
3. ✅ **Perfect MP alignment** - connection points stay locked
4. ✅ **Endpoint device sync** - table shows correct TP-1 and TP-2 devices
5. ✅ **Clear labeling** - purple "TP-1:" and "TP-2:" labels in table
6. ✅ **Better debugging** - console shows which devices at which TPs

---

## Benefits

### For Users

**Movement**:
- 🎯 Intuitive - click any part of BUL to move it
- 💪 Reliable - always moves as one unit
- ✨ Smooth - no jitter or separation

**Link Table**:
- 📊 Clear - shows endpoint devices with TP labels
- 🎨 Visual - purple color indicates BUL structure
- ✅ Accurate - always shows current TP-1 and TP-2 devices

### Technical

**Movement**:
- Simple delta calculation (no complex recursion)
- Stored initial positions prevent accumulation errors
- Works for any BUL length (2, 3, 4+ links)

**Device Sync**:
- Reuses existing TP detection logic (consistent with visual labels)
- Works with BUL rule (lower ID = TP-1)
- Handles edge cases (1 device, no devices, etc.)

---

## Related Features

All existing features still work:
- ✅ TP auto-stick (30px range)
- ✅ Green visual feedback
- ✅ All TP combinations work
- ✅ Lower-ID rule maintained
- ✅ MP dragging (route the BUL)
- ✅ Device attachment (orange feedback)

---

## Final Result

**One Unified BUL System**:
1. Create BUL from any TP combination ✅
2. Drag BUL from any UL body ✅
3. See correct endpoint devices in table ✅
4. Move as rigid unit ✅
5. Clear visual and data sync ✅

**Natural, intuitive, and fully functional!** 🎉







