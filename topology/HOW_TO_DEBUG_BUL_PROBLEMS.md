# How to Debug BUL Problems Using the Canvas
## Practical Guide - December 5, 2025

This guide shows you exactly how to use the canvas and debugging tools to identify and fix BUL (Bound-Unbound Link) problems.

---

## 🎯 Quick Start - 3 Steps

### Step 1: Open the App
```bash
cd /home/dn/CURSOR
python3 -m http.server 8080
# Then open: http://localhost:8080/index.html
```

### Step 2: Enable Debug Visualization
Click the **"Debug"** button in the top bar (or press the keyboard shortcut)
- This shows the **Link Type Labels** (QL/UL/BUL) above each link
- This displays **TP/MP numbering** on connection points

### Step 3: Open the Debugger Panel
The debugger panel should appear on the right side showing:
- Real-time logs of all operations
- BUL tracking data
- Connection point changes
- Link type conversions

---

## 🔧 Debug Tools Available on Canvas

### 1. **Link Type Labels** (Visual Overlay)
**Toggle:** Click "Link Type Labels" button in top bar

**What you'll see on canvas:**
```
Device1 ─────── QL ─────── Device2    (Quick Link - both ends attached)
Device1 ─────── BUL ──○              (Bound-Unbound - one end free)
        ○─────── UL ──○              (Unbound Link - both ends free)
```

**Purpose:** Instantly see what type each link is

**Usefulness:**
- ✅ Verify link type is correct
- ✅ Spot unexpected conversions (QL → BUL → UL)
- ✅ Track which links are part of BUL chains

---

### 2. **Connection Point Visualization** (Always Visible When Selected)

**What you'll see on canvas:**

#### TP (Tap Point) - Green circles with labels:
```
    Device
      |
     TP-1  ← Green dot, labeled "TP-1"
      |
   (link line)
```

#### MP (Moving Point) - Purple circles with labels:
```
   (link line)
      |
     MP-1  ← Purple dot, labeled "MP-1"
      |
   (link line)
```

#### Free Endpoints - Blue circles:
```
   (link line)
      |
      ○  ← Blue dot (draggable)
```

**How to trigger:**
- Click on any link to select it
- All connection points become visible
- Labels show numbering (TP-1, TP-2, MP-1, MP-2, etc.)

**What to look for:**
- ❌ **Wrong TP numbers**: TP-1 should be on lower device ID
- ❌ **Duplicate MP numbers**: Each MP in a chain should have unique number
- ❌ **Missing connection points**: Every merge should show a point
- ❌ **Misaligned endpoints**: Free endpoints should snap together when close

---

### 3. **Debugger Panel** (Right Side)

**Sections:**
1. **Log** - Real-time event stream
2. **BUL Info** - Current BUL chain details
3. **State** - Application state snapshot
4. **Bug Alerts** - Detected issues

**What to watch in logs:**
```
✓ Link created: link_5 (type: BUL)
✓ Endpoint attached to device_1
⚠️ TP numbering updated: TP-1 → TP-2
❌ BUG: Endpoint becomes undefined after detach!
```

**BUL-specific logs to watch for:**
- `Link type converted: QL → BUL` - Normal when detaching
- `TP renumbered` - Check if numbering is correct
- `MP created at merge point` - Verify MP position
- `Endpoint snap: distance=X` - Check snap behavior
- `Device detached from link` - Verify clean detachment

---

## 🐛 Common BUL Problems & How to Spot Them

### Problem 1: **TP Numbering Wrong**

**Symptoms on Canvas:**
- TP-1 and TP-2 are swapped
- Both endpoints labeled TP-1 or both TP-2
- TP numbers change randomly

**How to identify:**
1. Create a BUL (attach one end to device, leave other free)
2. Click on the link to select it
3. Look at the green "TP" circles
4. **Expected:** TP-1 on device with LOWER ID
5. **Bug:** TP-1 on wrong device or missing

**Debug in console:**
```javascript
// Open browser console (F12)
// Type:
let link = editor.selectedObject;
console.log('Device1 ID:', link.device1);
console.log('Device2 ID:', link.device2);
console.log('TP positions:', link.tp1, link.tp2);
```

---

### Problem 2: **MP Numbering Not Per-BUL**

**Symptoms on Canvas:**
- MP numbers skip (MP-1, MP-5, MP-9)
- Multiple chains share same MP numbers
- MP numbers don't restart at 1 for each BUL

**How to identify:**
1. Create a BUL chain (3+ links merged together)
2. Click on the chain
3. Look at purple "MP" circles
4. **Expected:** MP-1, MP-2, MP-3 (sequential from 1)
5. **Bug:** MP-15, MP-16, MP-17 (global counter)

**Fix location:** 
- See `CODE_SNAPSHOTS_CRITICAL_FUNCTIONS.md` - Snapshot 4
- File: `topology.js` - Look for `renumberChainMPs()` function

---

### Problem 3: **Endpoint Snap Not Working**

**Symptoms on Canvas:**
- Free endpoints don't attract when close
- Cursor doesn't change to "copy" icon near endpoints
- Endpoints overlap but don't merge

**How to identify:**
1. Create a UL (double-click background twice, fast)
2. Drag one blue endpoint near another blue endpoint
3. Watch cursor and endpoint behavior
4. **Expected:** 
   - Cursor changes to "copy" within 25px
   - Endpoint magnetically pulls toward target
   - Snaps together within 5px
5. **Bug:** No attraction, no snap, no cursor change

**Check in debugger:**
```
Look for logs:
- "UL snap distance: X px" (should appear when dragging)
- "Endpoint merged with: endpoint_Y" (when snapping)
```

---

### Problem 4: **Link Type Conversion Failure**

**Symptoms on Canvas:**
- Link shows "QL" but has free endpoint (should be BUL)
- Link shows "UL" but is attached to device (should be BUL)
- Link shows "BUL" but both ends attached (should be QL)

**How to identify:**
1. Enable "Link Type Labels" button
2. Look at labels above each link
3. Check endpoints:
   - QL = 2 green TPs (both attached)
   - BUL = 1 green TP + 1 blue endpoint (one attached, one free)
   - UL = 2 blue endpoints (both free)
4. **Bug:** Label doesn't match actual attachment state

**Fix location:**
- See `CODE_SNAPSHOTS_CRITICAL_FUNCTIONS.md` - Snapshot 2
- File: `topology.js` - Look for device detachment logic

---

### Problem 5: **Chain Merge Issues**

**Symptoms on Canvas:**
- Links don't merge when endpoints touch
- Merged links lose their connection
- MP appears at wrong location

**How to identify:**
1. Create 2 BULs with free endpoints near each other
2. Drag one endpoint to the other
3. **Expected:** 
   - Purple MP appears at merge point
   - Both links now in same chain
   - Can drag MP to adjust curve
4. **Bug:** 
   - No MP appears
   - Links stay separate
   - MP appears but can't be dragged

---

## 🧪 Testing Scenarios for BUL Problems

### Test 1: Basic BUL Creation
```
1. Add 2 devices
2. Click Link tool
3. Click device1
4. Click on empty canvas (NOT on device2)
5. ✓ Link should be labeled "BUL"
6. ✓ One green TP on device1
7. ✓ One blue endpoint floating free
```

### Test 2: QL → BUL Conversion (Detach)
```
1. Create QL between 2 devices
2. Click and drag one endpoint away from device
3. ✓ Label changes: "QL" → "BUL"
4. ✓ Green TP becomes blue endpoint
5. ✓ Device reference cleared
6. ✓ Debugger logs: "Device detached"
```

### Test 3: BUL → QL Conversion (Attach)
```
1. Create BUL with one free endpoint
2. Drag free endpoint near a device
3. ✓ Cursor changes to "crosshair" near device
4. ✓ Endpoint snaps to device edge
5. ✓ Label changes: "BUL" → "QL"
6. ✓ Blue endpoint becomes green TP
7. ✓ Debugger logs: "Device attached"
```

### Test 4: UL → BUL → QL Chain
```
1. Create UL (both ends free)
2. Drag one end to device1
3. ✓ "UL" → "BUL"
4. Drag other end to device2
5. ✓ "BUL" → "QL"
6. ✓ Both endpoints now green TPs
```

### Test 5: Multi-Link BUL Chain
```
1. Create BUL1 (device1 → free)
2. Create BUL2 (device2 → free)
3. Drag BUL1 free endpoint to BUL2 free endpoint
4. ✓ Purple MP appears at merge point
5. ✓ Can drag MP to adjust chain shape
6. ✓ MP labeled "MP-1"
7. Add BUL3 to chain
8. ✓ New MP labeled "MP-2"
9. ✓ MP numbers sequential (1, 2, 3...)
```

---

## 🔍 Using Browser Console for Deep Debugging

### Inspect Selected Link:
```javascript
// Open DevTools (F12), go to Console tab
let link = editor.selectedObject;
console.log('Link ID:', link.id);
console.log('Link Type:', link.linkType);
console.log('Origin Type:', link.originType);
console.log('Device 1:', link.device1);
console.log('Device 2:', link.device2);
console.log('Merged With:', link.mergedWith);
console.log('Merged Into:', link.mergedInto);
```

### Check All BULs in Topology:
```javascript
let buls = editor.objects.filter(o => o.linkType === 'BUL');
console.log('Total BULs:', buls.length);
buls.forEach(bul => {
    console.log(`${bul.id}: ${bul.device1 ? '●' : '○'}──${bul.device2 ? '●' : '○'}`);
});
```

### Verify TP Numbering:
```javascript
let link = editor.selectedObject;
let allLinks = editor.getAllMergedLinks(link);
console.log('Chain length:', allLinks.length);
allLinks.forEach((l, i) => {
    console.log(`Link ${i+1}:`, l.id, 'Device1:', l.device1, 'Device2:', l.device2);
});
```

### Monitor Endpoint Positions:
```javascript
// Watch endpoint positions in real-time
setInterval(() => {
    let link = editor.selectedObject;
    if (link && link.type === 'link') {
        let start = editor.getLinkStartPoint(link);
        let end = editor.getLinkEndPoint(link);
        console.log(`Start: (${Math.round(start.x)}, ${Math.round(start.y)})`);
        console.log(`End: (${Math.round(end.x)}, ${Math.round(end.y)})`);
    }
}, 1000); // Every 1 second
```

---

## 🎨 Visual Indicators on Canvas

### Color Coding:
- **Green circles** = TPs (attached to devices)
- **Purple circles** = MPs (merge points between links)
- **Blue circles** = Free endpoints (UL/BUL)
- **Gray lines** = Normal links
- **Blue highlight** = Selected link

### Cursor Changes:
- **Default arrow** = Normal mode
- **Crosshair** = Near device (can attach)
- **Copy icon** = Near endpoint (can merge)
- **Grab hand** = Can drag
- **Move arrows** = Dragging object

### Label Format:
```
Link Type:  QL    BUL    UL
            │     │      │
Connection: TP-1  TP-1   (none)
Points:     MP-1  MP-1   (none)
            TP-2  (free) (free)
```

---

## 📊 Debugger Panel Sections Explained

### 1. Real-Time Log (Top Section)
**Shows:**
- Every action as it happens
- Link creation, deletion, conversion
- Endpoint snap events
- TP/MP numbering changes
- Device attachment/detachment
- Bug alerts

**Color coding:**
- 🟢 Green = Success
- 🔵 Blue = Info
- 🟡 Yellow = Warning
- 🔴 Red = Error/Bug

### 2. BUL Info Section (Middle)
**Shows:**
- Current BUL chain details
- Number of links in chain
- TP positions and numbers
- MP positions and numbers
- Device attachments
- Chain structure diagram

**Example output:**
```
BUL Chain: link_5
├─ UL-1: link_5 (Device: device_1 → free)
├─ MP-1: (150, 200)
└─ UL-2: link_6 (free → free)
TPs: TP-1 @ device_1, TP-2 @ free
```

### 3. State Inspector (Bottom)
**Shows:**
- Current tool mode
- Selected object
- Drag/pan/zoom state
- Link modes (sticky, continuous, curve)
- Object counts

### 4. Bug Alerts (Bottom Banner)
**Shows:**
- Critical bugs detected automatically
- Severity level (CRITICAL/WARNING/INFO)
- Bug category (RACE_CONDITION, LOGIC_ERROR, etc.)
- Copy button for full bug report
- Link to related code section

---

## 🚨 When to Suspect a BUL Bug

### Red Flags:
1. ❌ Link type label doesn't match visual appearance
2. ❌ TP/MP numbers skip or duplicate
3. ❌ Endpoints don't snap when they should
4. ❌ Cursor doesn't change near snap targets
5. ❌ Link "jumps" to different position on release
6. ❌ Merged links lose connection randomly
7. ❌ MPs disappear or multiply unexpectedly
8. ❌ Console shows "undefined" errors
9. ❌ Debugger shows red error messages
10. ❌ Link table shows wrong device connections

---

## 🔧 Quick Fixes to Try

### Fix 1: Refresh Numbering
```
1. Select any link in the chain
2. Move it slightly (triggers renumbering)
3. Check if TP/MP labels update correctly
```

### Fix 2: Recreate Chain
```
1. Note the devices/positions
2. Delete all links in problematic chain
3. Recreate them one by one
4. Verify numbering at each step
```

### Fix 3: Clear and Restart
```
1. Save your topology (backup)
2. Refresh browser (F5)
3. Load topology
4. Test if problem persists
```

### Fix 4: Check Console for Errors
```
1. Open DevTools (F12)
2. Go to Console tab
3. Look for red error messages
4. Copy error and search in code
```

---

## 📝 Reporting a BUL Bug

If you find a bug, collect this info:

### 1. Bug Description
- What you were doing
- What you expected
- What actually happened

### 2. Visual Evidence
- Take screenshot showing:
  - Link type labels
  - TP/MP numbering
  - Debugger panel logs

### 3. Reproduction Steps
```
1. Create device_1 at (100, 100)
2. Create device_2 at (300, 100)
3. Create link from device_1 to (200, 150)
4. Observe: Label shows "QL" but should show "BUL"
```

### 4. Console Output
- Copy any red errors from console
- Copy debugger log entries related to the bug

### 5. Topology State
- Export topology JSON
- Include in bug report
- Helps reproduce exact scenario

---

## 💡 Pro Tips

### Tip 1: Use Grid for Alignment
- Enable grid (button in toolbar)
- Makes it easier to see if endpoints align
- Helps identify "snap distance" issues

### Tip 2: Zoom In for Precision
- Use mouse wheel to zoom in (up to 3x)
- Better visibility of connection points
- Easier to see label text

### Tip 3: Watch the Debugger During Actions
- Keep debugger panel open
- Perform action (create link, drag, merge)
- Watch real-time logs appear
- Spot exactly when bug occurs

### Tip 4: Test in Isolation
- Create fresh topology
- Add only devices needed for test
- Reproduce bug with minimal setup
- Easier to identify cause

### Tip 5: Compare Working vs Broken
- Create a working BUL chain
- Screenshot it
- Try to reproduce bug
- Compare visual differences

---

## 🎓 Understanding BUL Internals

### Link Object Structure:
```javascript
{
  id: 'link_5',
  type: 'link',
  linkType: 'BUL',           // Current type
  originType: 'UL',          // Original type when created
  device1: 'device_1',       // First endpoint (null if free)
  device2: null,             // Second endpoint (null if free)
  device1Angle: 1.57,        // Angle to device edge (radians)
  device2Angle: null,
  mergedWith: {              // If this link merges with another
    linkId: 'link_6',        // Next link in chain
    parentFreeEnd: 'end',    // Which end connects ('start' or 'end')
    childFreeEnd: 'start',
    mpNumber: 1              // MP number at this merge
  },
  mergedInto: {              // If this link is merged into another
    parentId: 'link_4',      // Previous link in chain
    endpoint: 'end'
  }
}
```

### Chain Structure:
```
Device1 ─┬─ link_4 (BUL) ─┬─ MP-1 ─┬─ link_5 (UL) ─┬─ MP-2 ─┬─ link_6 (BUL) ─○
         │                │        │                │        │                │
        TP-1         mergedWith   TP-2        mergedWith    TP-2           Free
                     (link_5)                  (link_6)                  Endpoint
```

---

## 📚 Related Documentation

- **APP_LOGIC_SNAPSHOTS.md** - Snapshot 3, 4: BUL system overview
- **CODE_SNAPSHOTS_CRITICAL_FUNCTIONS.md** - Snapshots 1-5: BUL algorithms
- **BUL_NUMBERING_SYSTEM.md** - Detailed TP/MP numbering rules
- **FINAL_BUL_FIX_SUMMARY.md** - Historical BUL bugs and fixes
- **topology.js** - Lines 1200-4800: BUL implementation

---

*End of BUL Debugging Guide*
*Created: December 5, 2025*



