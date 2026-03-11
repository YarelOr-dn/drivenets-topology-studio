# Critical Bug Fix: Free Endpoints Can Now Merge

## Problem

When two ULs were merged (Link A → Link B via connection point), Link B's FREE endpoint could not connect to a third UL. The free endpoint was incorrectly treated as a connection point and blocked from merging.

## Root Cause

The connection point detection logic was too aggressive:

```javascript
// OLD (WRONG) - Blocked ALL endpoints on child links
const startIsConnectionPoint = ... || (obj.mergedInto);
```

This marked ANY endpoint on a child link as a connection point, preventing it from being used for further merging.

## Solution

Now properly checks WHICH endpoint is the connection point vs the free endpoint:

```javascript
// NEW (CORRECT) - Only blocks actual connection points
if (obj.mergedInto) {
    const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
    if (parentLink && parentLink.mergedWith) {
        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
        startIsConnectionPoint = (childFreeEnd !== 'start'); // Only block if NOT free
    }
}
```

## What Changed

### Fixed in 2 Functions:

1. **`handleMouseUp()` UL snapping** (Lines 3347-3416)
   - Now correctly identifies free vs connected endpoints
   - Free endpoints can merge with other ULs ✅
   - Connection points still blocked from merging 🚫

2. **`findUnboundLinkEndpoint()`** (Lines 7674-7729)
   - Now correctly identifies free vs connected endpoints
   - Free endpoints can be dragged to create merges ✅
   - Connection points not draggable 🚫

## Behavior Now

### Example: Creating a 3-Link Chain

```
Step 1: Merge UL1 + UL2
UL1 ----🟣---- UL2
        ^
   Connection point
   
Step 2: Drag UL2's FREE endpoint to UL3
UL1 ----🟣---- UL2 🔘  🔘 UL3
                  ^     ^
            Free endpoint can merge! ✅

Step 3: Result - 3-link chain
UL1 ----🟣---- UL2 ----🟣---- UL3
```

### What Works ✅

- **Free endpoints** can merge with other ULs
- **Free endpoints** can be dragged to create new merges
- **Connection points** still blocked (visual only)
- **Infinite chains** possible (UL1 → UL2 → UL3 → UL4...)

### What's Blocked 🚫

- **Connection points** cannot merge with other ULs
- **Connection points** cannot be dragged independently
- **Device-attached** endpoints remain blocked from merging

## Visual Guide

```
Link B in a merge:
UL_A ----🟣 Connection Point 🟣---- Link B ----🔘 Free Endpoint

FREE ENDPOINT (🔘):
- Gray circle
- Can be dragged ✅
- Can merge with other ULs ✅
- Can attach to devices ✅

CONNECTION POINT (🟣):
- Purple circle  
- Cannot be dragged 🚫
- Cannot merge with ULs 🚫
- Visual indicator only
```

## Test Scenario

1. Create 3 ULs: **UL1**, **UL2**, **UL3**
2. Merge **UL1** + **UL2** → Connection point forms 🟣
3. Drag **UL2's free endpoint** near **UL3** → Should merge! ✅
4. Result: **UL1 → UL2 → UL3** all connected
5. All 3 links highlight when any is selected ✨

## Technical Details

### Data Structure Review

**Parent Link (has mergedWith):**
```javascript
{
    mergedWith: {
        linkId: 'child_id',
        parentFreeEnd: 'start',  // Parent's FREE endpoint
        childFreeEnd: 'end'       // Child's FREE endpoint
    }
}
```

**Child Link (has mergedInto):**
```javascript
{
    mergedInto: {
        parentId: 'parent_id',
        connectionPoint: { x, y }
    }
}
```

**Logic:**
- If `childFreeEnd === 'start'` → Child's **start** is FREE, **end** is connected
- If `childFreeEnd === 'end'` → Child's **end** is FREE, **start** is connected

### Key Changes

**Before:**
```javascript
// Marked ALL endpoints on child as connection points
const startIsConnectionPoint = ... || (obj.mergedInto);
```

**After:**
```javascript
// Only marks the ACTUAL connection point
if (obj.mergedInto) {
    const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
    if (parentLink && parentLink.mergedWith) {
        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
        startIsConnectionPoint = (childFreeEnd !== 'start');
    }
}
```

## Impact

- ✅ **Fixed** critical bug preventing chain extension
- ✅ **Infinite chains** now work properly
- ✅ **Free endpoints** correctly identified and usable
- ✅ **Connection points** still blocked as intended
- ✅ **No breaking changes** to existing merged links

## Files Modified

- `topology.js` - Lines 3347-3416, 7674-7729

