# BUL Movement Rules - Complete Specification

## Core Principles

### 1. **Always 2 TPs at BUL Edges** ✅
No matter how many ULs are in a BUL, there are **exactly 2 Terminal Points (TPs)** - one at each end of the chain.

### 2. **Links Keep Position When Merging** ✅
When connecting ULs together:
- The **existing link stays in place**
- The **new link moves to snap** to the existing link
- No jumping or shifting of already-placed links

### 3. **Only MP Moves Its 2 Connected ULs** ✅
When dragging an MP (Moving Point):
- **ONLY the 2 ULs** directly connected to that MP move
- **All other ULs** in the chain stay fixed in position
- Each MP is independent

---

## Detailed Behavior

### Structure of a BUL

```
5-Link BUL Example:

TP ━━ UL1 ━━ MP1 ━━ UL2 ━━ MP2 ━━ UL3 ━━ MP3 ━━ UL4 ━━ MP4 ━━ UL5 ━━ TP
⚪                🟣           🟣           🟣           🟣                ⚪
(free)      (connection) (connection) (connection) (connection)      (free)

Elements:
- 5 ULs (unbound links)
- 2 TPs (gray dots at ends - free endpoints)
- 4 MPs (purple dots - connection points between ULs)
- N links → 2 TPs + (N-1) MPs
```

---

## Movement Scenarios

### Scenario 1: Merging Links

**Action**: Drag UL3's TP to connect to UL1--MP1--UL2 chain

#### Before:
```
UL1 ━━ MP1 ━━ UL2               UL3
TP           TP                 TP  TP
```

#### Process:
1. User grabs UL3's TP
2. Drags it near UL2's free TP
3. UL3 snaps to UL2's position
4. MP2 is created at the connection point

#### After:
```
UL1 ━━ MP1 ━━ UL2 ━━ MP2 ━━ UL3
TP                          TP
```

**Key Points**:
- ✅ UL1 didn't move
- ✅ UL2 didn't move
- ✅ UL3 moved to snap to UL2
- ✅ New MP2 created where they connect
- ✅ Still exactly 2 TPs (at UL1 and UL3 ends)

---

### Scenario 2: Dragging an MP (Middle of Chain)

**Action**: Drag MP2 (between UL2 and UL3) in a 4-link BUL

#### Before:
```
UL1 ━━ MP1 ━━ UL2 ━━ MP2 ━━ UL3 ━━ MP3 ━━ UL4
TP                  ↑                       TP
                  Grab this MP
```

#### During Drag:
```
UL1 ━━ MP1 ━━ UL2     MP2 (dragged up)
TP             \       |
                \     /
                 UL3 ━━ MP3 ━━ UL4
                              TP
```

#### What Moves:
- ✅ **MP2** follows mouse
- ✅ **UL2's end** (connected to MP2) moves with MP2
- ✅ **UL3's start** (connected to MP2) moves with MP2
- 🔒 **UL1** stays fixed (not connected to MP2)
- 🔒 **UL4** stays fixed (not connected to MP2)
- 🔒 **MP1** stays fixed
- 🔒 **MP3** stays fixed

**Key Points**:
- ✅ Only UL2 and UL3 move (the 2 links touching MP2)
- ✅ UL1 and UL4 stay fixed
- ✅ All TPs and other MPs stay fixed
- ✅ The BUL can be "bent" at MP2

---

### Scenario 3: Dragging an MP (At Edge)

**Action**: Drag MP1 (between UL1 and UL2) in a 3-link BUL

#### Before:
```
UL1 ━━ MP1 ━━ UL2 ━━ MP2 ━━ UL3
TP      ↑                   TP
      Grab this
```

#### During Drag:
```
    MP1 (dragged)
   /   \
UL1     UL2 ━━ MP2 ━━ UL3
TP                      TP
```

#### What Moves:
- ✅ **MP1** follows mouse
- ✅ **UL1's end** (connected to MP1) moves with MP1
- ✅ **UL2's start** (connected to MP1) moves with MP1
- 🔒 **UL3** stays fixed
- 🔒 **MP2** stays fixed

---

### Scenario 4: Dragging a TP (Free Endpoint)

**Action**: Drag a TP at the end of a BUL

#### Before:
```
UL1 ━━ MP1 ━━ UL2 ━━ MP2 ━━ UL3
TP                          TP ← Grab this
```

#### During Drag:
```
UL1 ━━ MP1 ━━ UL2 ━━ MP2 ━━ UL3
TP                           \
                              \ TP (dragged)
```

#### What Moves:
- ✅ **TP** follows mouse
- ✅ **UL3's end** moves with the TP
- 🔒 **UL1** stays fixed
- 🔒 **UL2** stays fixed
- 🔒 **MP1** and **MP2** stay fixed

**Key Point**: Free TPs can be moved to:
- Route the link around obstacles
- Connect to devices
- Connect to other UL TPs (create new MP)

---

## Implementation Details

### When Merging Links (Creating MP)

**Code Location**: `topology.js` lines 3945-3952

```javascript
// Snap the NEW link's endpoint to the EXISTING link's endpoint
// The existing link stays in place - only the new link moves to connect
if (this.stretchingEndpoint === 'start') {
    this.stretchingLink.start.x = nearbyULEndpoint.x;
    this.stretchingLink.start.y = nearbyULEndpoint.y;
}
```

**What This Does**:
- Moves the dragging link's endpoint to the target position
- Does NOT move the existing link
- Creates connection point (MP) at the merge location

---

### When Dragging an MP

**Code Location**: `topology.js` lines 2569-2632

```javascript
if (this.stretchingConnectionPoint) {
    // 1. Move the grabbed link's endpoint to mouse position
    if (this.stretchingEndpoint === 'start') {
        this.stretchingLink.start.x = newX;
        this.stretchingLink.start.y = newY;
    }
    
    // 2. Find the partner link
    if (this.stretchingLink.mergedWith) {
        partnerLink = this.objects.find(o => o.id === this.stretchingLink.mergedWith.linkId);
        partnerEndpoint = /* which end is connected */;
    }
    
    // 3. Move partner link's connected endpoint
    if (partnerLink && partnerEndpoint) {
        if (partnerEndpoint === 'start') {
            partnerLink.start.x = newX;
            partnerLink.start.y = newY;
        }
    }
    
    // 4. Update metadata (does NOT move other links)
    this.updateAllConnectionPoints();
}
```

**What This Does**:
1. Moves ONE endpoint of the grabbed link
2. Moves ONE endpoint of the partner link
3. Updates all MP metadata (connectionPoint x,y) to match
4. **Does NOT move** any other links in the chain

---

### Critical: `updateAllConnectionPoints()` Does NOT Move Links

**Code Location**: `topology.js` lines 6501-6541

This function:
- ✅ **READS** from `link.start.x`, `link.end.x` (current positions)
- ✅ **WRITES** to `link.mergedWith.connectionPoint.x` (metadata only)
- ❌ **NEVER WRITES** to `link.start.x` or `link.end.x`

```javascript
updateAllConnectionPoints() {
    this.objects.forEach(link => {
        if (link.mergedWith) {
            // READ link's current endpoint position
            const newConnectionX = link.end.x; // Just reading!
            
            // WRITE to metadata only
            link.mergedWith.connectionPoint.x = newConnectionX;
            
            // Does NOT write to link.end.x or link.start.x
        }
    });
}
```

**Purpose**: Keeps MP metadata synchronized with actual link positions, but doesn't cause movement.

---

## Debugging and Verification

### Debug Messages

When grabbing an MP, you'll see:

```
🎯 UL Grabbed: link_234 (end)
   Chain size: 4 link(s)
   Point type: MP (Connection Point)
   🟣 MP Drag: Only link_234 and link_345 will move
   🔒 Other 2 link(s) in chain will stay fixed
```

This confirms:
- Which links will move (the 2 touching the MP)
- How many links will stay fixed
- That it's an MP drag (not a TP drag)

---

## Visual Guide

### MP Dragging Behavior

```
Before:
═══════════════════════════════════════
     TP                          TP
      |                           |
    UL1 ━━━━━━ MP1 ━━━━━━ UL2 ━━━━━━ MP2 ━━━━━━ UL3
                ↑
           Grab MP1

During:
═══════════════════════════════════════
     TP                               TP
      |           MP1 (dragged)        |
    UL1            /  \          UL2 ━━━━━━ MP2 ━━━━━━ UL3
   (moves)    (moves)           (fixed)  (fixed)  (fixed)
   
Result:
- UL1 and UL2 bend at MP1
- UL3 stays in place
- MP2 stays in place
```

---

## Testing Checklist

### Test 1: Merge Without Jumping
1. Create 2 ULs in different positions
2. Drag one TP to the other
3. ✅ **Verify**: First link didn't move
4. ✅ **Verify**: Second link snapped to first
5. ✅ **Verify**: MP created at connection
6. ✅ **Verify**: 2 TPs visible (at ends)

### Test 2: MP Moves Only 2 Links
1. Create 4-link BUL: UL1--MP1--UL2--MP2--UL3--MP3--UL4
2. Grab MP2 and drag it
3. ✅ **Verify**: UL2 and UL3 move
4. ✅ **Verify**: UL1 and UL4 stay fixed
5. ✅ **Verify**: MP1 and MP3 stay fixed
6. ✅ **Verify**: Still 2 TPs at ends

### Test 3: Long Chain Independence
1. Create 5-link BUL
2. Drag MP1 (between UL1 and UL2)
3. ✅ **Verify**: Only UL1 and UL2 move
4. ✅ **Verify**: UL3, UL4, UL5 stay fixed
5. Drag MP3 (between UL3 and UL4)
6. ✅ **Verify**: Only UL3 and UL4 move
7. ✅ **Verify**: UL1, UL2, UL5 stay fixed

---

## Summary

### Core Rules ✅

1. **2 TPs Always**: N links → 2 TPs + (N-1) MPs
2. **No Jump on Merge**: Existing links stay in place
3. **Localized MP Movement**: Only 2 connected ULs move per MP
4. **Independent MPs**: Each MP controls only its 2 links

### Implementation ✅

- ✅ Merge logic snaps new link to existing
- ✅ MP drag moves only 2 endpoints
- ✅ `updateAllConnectionPoints()` only updates metadata
- ✅ Debug messages confirm movement scope

### User Experience ✅

- ✅ Predictable: Links don't unexpectedly move
- ✅ Flexible: Can bend BUL at any MP
- ✅ Controllable: Each MP independent
- ✅ Clear: Visual feedback shows what moves

---

*Document created: 2025-11-27*  
*Status: Specification Complete ✅*  
*Implementation: Verified Working ✅*










