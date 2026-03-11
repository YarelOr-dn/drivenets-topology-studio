# Fix: BUL Jumps in Multi-Select Mode

## Problem
When selecting and dragging 3+ ULs in a BUL chain together (multi-select mode), the connection points (MPs) would jump and become inconsistent. The BUL structure would break, with MPs appearing at wrong locations.

### Reported Issue
- **Severity**: HIGH
- **Affected**: Multi-select dragging of merged ULs (BULs)
- **Symptom**: "Jumps" detected when moving 3+ link BULs
- **Context**: "Unbound link moved in MS mode (merged unit)"

### Expected Behavior
When dragging a complete BUL chain:
```
Before:  UL1 --MP1-- UL2 --MP2-- UL3
         TP          MPs          TP

After dragging all together:
         UL1 --MP1-- UL2 --MP2-- UL3  (moved as unit)
         TP          MPs          TP
         
✅ 2 TPs at ends
✅ 2 MPs at connection points
✅ No jumps or inconsistencies
```

### Actual Behavior (Before Fix)
When dragging with all links selected:
```
Before:  UL1 --MP1-- UL2 --MP2-- UL3
         
After drag: UL1   MP1???  UL2  MP2???  UL3
         
❌ MPs jump to wrong positions
❌ Connection points become inconsistent
❌ BUL structure breaks
```

## Root Cause

### The Conflict
In multi-select mode, when ALL links in a BUL are selected:

1. **UL1** (parent) tries to:
   - Move its own endpoints from initial position
   - Update connection point with UL2
   - Move UL2 to maintain connection

2. **UL2** (middle link) tries to:
   - Move its own endpoints from initial position
   - Update connection point with UL1 (as child)
   - Update connection point with UL3 (as parent)
   - Move UL1 to maintain connection
   - Move UL3 to maintain connection

3. **UL3** (child) tries to:
   - Move its own endpoints from initial position
   - Update connection point with UL2
   - Move UL2 to maintain connection

### The Problem
Each link was independently calculating and setting connection points, causing:
- **Conflicting updates**: UL1 sets MP1 position, then UL2 overwrites it
- **Cumulative offsets**: Movement gets applied multiple times
- **Position jumping**: Connection points end up at incorrect locations

### Code Location
**File**: `topology.js`  
**Lines**: 3146-3204 (multi-select dragging logic)

The issue was in this section:
```javascript
// OLD (BROKEN) - Always tried to move partner
if (obj.mergedWith) {
    const childLink = this.objects.find(...);
    if (childLink && !this.selectedObjects.includes(childLink)) {
        // Move child... BUT this check wasn't enough!
    }
}
```

The problem: Even though it checked `!this.selectedObjects.includes(childLink)`, BOTH links were trying to update the SAME connection point metadata, causing conflicts.

## Solution

### Fix 1: Check Partner Selection BEFORE Any Updates
**Location**: Lines 3146-3230

Added check at the START to determine if the partner link is in selection:

```javascript
// NEW (FIXED) - Check partner selection first
let partnerInSelection = false;
if (obj.mergedWith) {
    const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
    partnerInSelection = childLink && this.selectedObjects.includes(childLink);
} else if (obj.mergedInto) {
    const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
    partnerInSelection = parentLink && this.selectedObjects.includes(parentLink);
}

// Only do partner dragging if partner is NOT selected
if (!partnerInSelection) {
    // ... partner moving logic ...
}
// If partner IS in selection, they move together naturally
```

### Fix 2: Update All Connection Points After Movement
**Location**: Lines 3277-3280

Added explicit call to `updateAllConnectionPoints()` at the end of multi-select dragging:

```javascript
// CRITICAL: Update all connection points after multi-select dragging
// This ensures MPs stay synchronized when dragging 3+ link BULs
this.updateAllConnectionPoints();

this.draw();
return;
```

### How It Works Now

#### Scenario: Dragging Complete BUL (UL1--MP1--UL2--MP2--UL3)

**Step 1: Initial Selection**
- User selects all 3 links (MS mode)
- All stored in `multiSelectInitialPositions`

**Step 2: During Drag**
- Each link moves from its initial position + dx/dy
- NO partner moving attempts (all are in selection)
- NO conflicting connection point updates

**Step 3: After Movement**
- All links have moved to new positions
- `updateAllConnectionPoints()` called ONCE
- Recalculates ALL MPs based on actual endpoint positions
- All connection points synchronized correctly

#### Scenario: Dragging Partial BUL (Only UL1 selected)

**Step 1: Selection**
- User selects only UL1
- UL2 and UL3 not selected

**Step 2: During Drag**
- UL1 moves
- UL1 detects UL2 is NOT in selection
- UL1 moves UL2 to maintain connection
- UL2 then moves UL3 (cascade)
- Connection points updated during cascade

**Step 3: Result**
- Entire BUL moves as unit (even though only UL1 selected)
- Connection points maintained correctly

## Technical Details

### Modified Sections

#### 1. Partner Selection Check (Lines 3146-3162)
```javascript
// Check if partner is in selection first
let partnerInSelection = false;
if (obj.mergedWith) {
    const childLink = this.objects.find(o => o.id === obj.mergedWith.linkId);
    partnerInSelection = childLink && this.selectedObjects.includes(childLink);
} else if (obj.mergedInto) {
    const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
    partnerInSelection = parentLink && this.selectedObjects.includes(parentLink);
}
```

#### 2. Conditional Partner Movement (Lines 3163-3227)
```javascript
// Only do partner dragging if partner is NOT selected
if (!partnerInSelection) {
    // Move partner logic here
}
// If partner IS in selection, connection points will be updated by updateAllConnectionPoints() at the end
```

#### 3. Final Synchronization (Lines 3277-3280)
```javascript
// Update all connection points after multi-select dragging
this.updateAllConnectionPoints();
```

### Connection Point Update Logic

The `updateAllConnectionPoints()` function (lines 6424-6464) ensures:
1. For each parent link: Update its `mergedWith.connectionPoint` from actual endpoint position
2. For each child link: Update its `mergedInto.connectionPoint` from actual endpoint position
3. Both sides of each MP are synchronized

## Testing

### Test Scenario 1: Complete BUL Selection
1. Create UL1--MP1--UL2--MP2--UL3
2. Select all 3 links (marquee selection)
3. Drag the selection
4. **Verify**: All links move together, MPs stay at connection points
5. **Verify**: No jumps, no console errors
6. **Verify**: Link table shows correct structure: "3 UL(s) • 2 MP(s) • 2 TP(s)"

### Test Scenario 2: Partial BUL Selection
1. Create UL1--MP1--UL2--MP2--UL3
2. Select only UL1
3. Drag UL1
4. **Verify**: Entire BUL moves as unit
5. **Verify**: MPs stay at connection points

### Test Scenario 3: Long Chain (5+ Links)
1. Create UL1--MP1--UL2--MP2--UL3--MP3--UL4--MP4--UL5
2. Select all 5 links
3. Drag the selection
4. **Verify**: All MPs stay correct (4 MPs between 5 links)
5. **Verify**: 2 TPs at ends only
6. **Verify**: No jumps or inconsistencies

### Test Scenario 4: Mixed Selection (BUL + Devices)
1. Create devices D1 and D2
2. Create UL1--MP1--UL2--MP2--UL3
3. Attach UL1's TP to D1, UL3's TP to D2
4. Select D1, all ULs, and D2
5. Drag the selection
6. **Verify**: Everything moves together, MPs stay correct

## Performance Impact

### Before Fix
- O(n²) complexity: Each of n links updating connection points for its partners
- Redundant calculations and conflicting writes
- Jump detection overhead

### After Fix
- O(n) during drag: Each link moves once
- O(n) after drag: Single pass to update all connection points
- No conflicts, no jumps

## Summary

### The Fix
✅ **Check partner selection BEFORE moving**: Prevents conflicting updates  
✅ **Skip partner movement if selected**: Links move from initial positions  
✅ **Update all MPs after drag**: Single synchronized update  
✅ **No conflicts**: Each connection point updated once  

### Benefits
✅ **No jumps**: BULs stay consistent during multi-select drag  
✅ **Correct structure**: Always 2 TPs + (N-1) MPs for N links  
✅ **Better performance**: O(n) instead of O(n²)  
✅ **Reliable**: Works for any BUL length (2, 3, 10+ links)  

### Files Modified
- `topology.js` - Lines 3146-3280 (multi-select dragging logic)

### Related Documentation
- `FIX_MPs_AFTER_MS_MOVING.md` - MPs working after movement
- `FIX_MP_STICKING.md` - MP not sticking to cursor
- `BUL_RULES_IMPLEMENTATION.md` - Complete BUL rules
- `MOVING_POINTS_MPs.md` - MP dragging behavior

---

*Fix applied: 2025-11-27*  
*Issue: BUL jumps in multi-select mode*  
*Status: RESOLVED ✅*










