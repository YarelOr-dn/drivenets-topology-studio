# Fix: MP Dragging Incorrectly Moves TPs
## Issue Report - December 5, 2025

## 🐛 Problem Description

**What's happening:**
When dragging an MP (purple merge point between links), the TPs (green tap points on devices) are also moving.

**Expected behavior:**
- MPs should be draggable to adjust link curves
- TPs should stay attached to their devices (not move when MP moves)
- Only the MP should move, creating a curve in the link chain

**Visual example:**
```
Before drag:
Device1 ────TP-1────MP-1────TP-2──── Device2
             🟢      🟣       🟢

Current (WRONG):
User drags MP-1 down, but TP-2 also moves:
Device1 ────TP-1────┐
             🟢      │
                    MP-1 (moved down)
                     🟣
                     │
                    TP-2 (SHOULDN'T move!)
                     🟢
                     │
                    Device2

Expected (CORRECT):
User drags MP-1 down, only MP moves:
Device1 ────TP-1────┐         TP-2──── Device2
             🟢      │          🟢
                    MP-1 (moved down)
                     🟣
```

---

## 🔍 Root Cause

The issue is likely in how the link dragging code handles BUL (Bound-Unbound Link) chains. When an MP is dragged:

1. ✅ **Correct:** MP position should update
2. ❌ **Wrong:** Code is also updating connected TP positions
3. **Why:** TPs might be treated as regular draggable points instead of device-attached points

---

## 🛠️ Diagnostic Steps

### Step 1: Reproduce the Issue
1. Create 2 devices
2. Create a BUL chain (3+ links merged together)
3. Click on the chain to see connection points
4. Drag a purple MP (merge point)
5. Observe if green TPs on devices also move

### Step 2: Check Console
Open browser console (F12) and watch for:
- Errors during MP drag
- Messages about TP updates
- Position logging

### Step 3: Identify the Drag Logic
The problem is in the mouse move handler where MPs are being dragged. Look for:
- Code that updates MP positions
- Code that might be updating TP positions alongside MPs
- Merge point handling logic

---

## 💡 Likely Fix Locations

### Location 1: MP Drag Handler
Search in `topology.js` for where MPs are being moved:

```javascript
// WRONG - Updates both MP and connected points
if (draggingMP) {
    mp.x = mouseX;
    mp.y = mouseY;
    // BUG: Also updates TPs - SHOULD NOT!
    updateConnectedPoints(mp);
}

// CORRECT - Only update MP position
if (draggingMP) {
    mp.x = mouseX;
    mp.y = mouseY;
    // DON'T update TPs - they're attached to devices!
    // TPs should only update when device moves
}
```

### Location 2: Connection Point Update Logic
```javascript
// WRONG - Updates all connection points
function updateConnectionPoint(point) {
    point.x = newX;
    point.y = newY;
    // Updates both MPs AND TPs
}

// CORRECT - Only update if it's an MP
function updateConnectionPoint(point) {
    if (point.type === 'MP' || point.isMergePoint) {
        point.x = newX;
        point.y = newY;
    }
    // TPs are calculated from device positions
}
```

### Location 3: Link Chain Update
```javascript
// WRONG - Propagates movement to entire chain
function updateChainPoints(chain) {
    chain.forEach(link => {
        updateAllPoints(link); // Updates MPs AND TPs
    });
}

// CORRECT - Only update free points (MPs)
function updateChainPoints(chain) {
    chain.forEach(link => {
        updateMPsOnly(link); // Only update merge points
        // TPs recalculated from device positions
    });
}
```

---

## 🔧 Quick Fix (If You Know JavaScript)

### Step 1: Find the Dragging Code
Search for where connection points are being dragged:
```bash
# In topology.js, search for:
- "dragging.*connection"
- "MP.*drag"
- "mergePoint.*move"
```

### Step 2: Add TP Check
Before updating any point position, check if it's a TP:

```javascript
// Add this check before updating position
if (point.isTP || point.attachedToDevice) {
    // Skip - TPs should not be manually moved
    return;
}

// Only update MPs
point.x = newX;
point.y = newY;
```

### Step 3: Separate TP Calculation
TPs should be recalculated from device positions:

```javascript
// TPs are calculated, not dragged
function getTPPosition(link, endpoint) {
    if (endpoint === 'start' && link.device1) {
        const device = getDevice(link.device1);
        const angle = link.device1Angle || 0;
        return {
            x: device.x + Math.cos(angle) * device.radius,
            y: device.y + Math.sin(angle) * device.radius
        };
    }
    // Similar for endpoint 'end'
}
```

---

## 🎯 Temporary Workaround

Until fixed, you can work around this by:

1. **Don't drag MPs** - They'll move TPs too
2. **Recreate the chain** - Delete and remake if curve is wrong
3. **Move devices instead** - Adjust topology by moving devices

---

## 📊 Code Search Commands

To find the problematic code, search for:

```bash
# In topology.js:
grep -n "mergedWith" topology.js
grep -n "connectionPoint" topology.js  
grep -n "MP.*position" topology.js
grep -n "TP.*position" topology.js
```

Look for code that:
- Updates positions during drag
- Handles merge point movement
- Propagates changes through link chains

---

## 🔍 Debug Information Needed

To fix this properly, we need to know:

1. **When does it happen?**
   - Always when dragging MPs?
   - Only with certain link configurations?
   - Only in specific BUL chains?

2. **Which TPs move?**
   - All TPs in the chain?
   - Only TPs connected to the MP being dragged?
   - Random TPs?

3. **How much do they move?**
   - Same distance as MP?
   - Different amount?
   - In same direction?

4. **Console errors?**
   - Any errors when dragging?
   - Warnings about positions?
   - Debug messages?

---

## 📝 To Report This Bug Properly

Please provide:

1. **Steps to reproduce:**
   ```
   1. Add device A at (100, 100)
   2. Add device B at (300, 100)
   3. Create BUL from A
   4. Create BUL from B
   5. Merge the free endpoints (creates MP-1)
   6. Drag MP-1 down by 50px
   7. Observe: TP on device B also moves down
   ```

2. **Browser console output:**
   - Copy any error messages
   - Copy debug log entries during drag
   - Note any warnings

3. **Topology state:**
   - Export topology JSON before bug
   - Note device IDs involved
   - Note link IDs involved

---

## 🚀 Ideal Solution

The fix should ensure:

1. ✅ **MPs are freely draggable** - User can adjust curves
2. ✅ **TPs stay on devices** - Always attached, never move independently  
3. ✅ **Device movement updates TPs** - When device moves, its TPs follow
4. ✅ **Link curves update** - Curves recalculate when MPs or devices move
5. ✅ **No position jumps** - Smooth, predictable movement

---

## 🎓 Technical Background

### Point Types in BUL System:

**TP (Tap Point):**
- Green circles (🟢)
- Attached to device edges
- Position = device.center + (angle × radius)
- SHOULD NOT be draggable independently
- Update ONLY when device moves

**MP (Moving/Merge Point):**
- Purple circles (🟣)
- Free-floating waypoints
- Position = independent x, y coordinates
- SHOULD be freely draggable
- Creates curves in link chains

**Free Endpoints:**
- Blue circles (🔵)
- Not attached to anything
- Fully draggable
- Can snap to devices or other endpoints

---

## 📞 Next Steps

**Option A: Quick workaround**
- Avoid dragging MPs for now
- Adjust curves by moving devices

**Option B: Debug and fix**
- Enable debugger
- Watch console during MP drag
- Identify exact code causing TP movement
- Apply fix from suggestions above

**Option C: Revert to older version**
- If this is a new bug, try Dec 4 backups:
  ```bash
  cd /home/dn/CURSOR
  cp topology.js.backup_before_bul_removal topology.js
  ```

---

*Issue documented: December 5, 2025*
*Waiting for: Code inspection or more debug info*



