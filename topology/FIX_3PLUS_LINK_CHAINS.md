# Fix: 3+ Link Chains Detaching and Acting Weird

## Problem

When connecting a third link (or more) to a BUL (Bound Unbound Link) chain, the link would detach and act weird when:
- Grabbing MPs (Moving Points)
- Grabbing the link surface
- Dragging any part of the chain

## Root Cause

The merge logic had several issues when handling chains of 3+ links:

1. **Overwriting Existing Merges**: When connecting a third link, the code would overwrite existing `mergedWith` relationships instead of extending the chain
2. **Incorrect Parent/Child Assignment**: The logic assumed the stretching link was always the parent, but it could already be a child in a chain
3. **Connection Point Detection**: Only checked immediate parent/child relationships, not all connection points in long chains
4. **Chain Extension Logic**: When extending a chain, the free end calculation was incorrect

## Solution

### 1. Enhanced Merge Logic (Lines 3450-3565)

**Before**: Simple parent/child assignment that would overwrite existing relationships

**After**: Smart chain extension that:
- Detects if either link is already part of a chain
- Finds the correct place to attach (free TP of the chain)
- Extends the chain instead of overwriting
- Handles all cases: parent-to-parent, child-to-child, parent-to-child, child-to-parent

**Key Logic:**
```javascript
// Case 1: StretchingLink is already a parent
if (parentLink.mergedWith) {
    // Find the end of the chain and attach there
    let chainEnd = this.objects.find(o => o.id === parentLink.mergedWith.linkId);
    while (chainEnd && chainEnd.mergedWith) {
        chainEnd = this.objects.find(o => o.id === chainEnd.mergedWith.linkId);
    }
    parentLink = chainEnd; // Attach to end of chain
}

// Case 2: ChildLink is already a parent
if (childLink.mergedWith) {
    // Check if we're connecting to its free end
    // If yes, swap parent/child roles
}

// Case 3: Extend chain correctly
if (parentLink.mergedWith) {
    // Find chain end and attach new link there
    chainEnd.mergedWith = { linkId: childLink.id, ... };
}
```

### 2. Enhanced Connection Point Detection (Lines 7933-7963)

**Before**: Only checked immediate parent/child connection points

**After**: Checks ALL connection points in the entire chain

```javascript
// Get all links in the merge chain
const allMergedLinks = this.getAllMergedLinks(obj);

// Check all connection points in the chain
for (const chainLink of allMergedLinks) {
    // Check parent connection point
    if (chainLink.mergedWith && chainLink.mergedWith.connectionPoint) {
        // Check distance to connection point
    }
    // Check child connection point
    if (chainLink.mergedInto && chainLink.mergedInto.connectionPoint) {
        // Check distance to connection point
    }
}
```

### 3. Chain End Free End Calculation (Lines 3520-3540)

**Before**: Used incorrect free end calculation when extending chains

**After**: Correctly calculates the free end of the chain end link

```javascript
// Determine chainEnd's free end (opposite of where it's connected to parent)
let chainEndFreeEnd = 'end'; // Default
if (chainEnd.mergedInto) {
    const chainEndParent = this.objects.find(o => o.id === chainEnd.mergedInto.parentId);
    if (chainEndParent && chainEndParent.mergedWith) {
        const chainEndConnectedEnd = chainEndParent.mergedWith.childFreeEnd;
        chainEndFreeEnd = chainEndConnectedEnd === 'start' ? 'end' : 'start';
    }
}
```

### 4. Connection Point Sync (Line 3558)

Added `updateAllConnectionPoints()` call after merge to ensure all connection points in the chain are synced correctly.

## Technical Details

### Files Modified

1. **topology.js** - Lines 3450-3565 (merge logic)
2. **topology.js** - Lines 7933-7963 (connection point detection)
3. **topology.js** - Line 3558 (connection point sync)

### How It Works Now

**Scenario 1: Connecting Third Link**
```
Link A ----🟣 MP1 ---- Link B
                  🔘 TP (free)
                   ↑
              Link C (new)
```

**Process:**
1. Detect Link B is already a child (has `mergedInto`)
2. Find Link B's free TP
3. Attach Link C to Link B's free end
4. Link B becomes parent, Link C becomes child
5. Result: `A → B → C` chain ✅

**Scenario 2: Connecting to Chain End**
```
Link A ----🟣 MP1 ---- Link B ----🟣 MP2 ---- Link C
                                              🔘 TP (free)
                                               ↑
                                          Link D (new)
```

**Process:**
1. Detect Link A is a parent (has `mergedWith`)
2. Find end of chain (Link C)
3. Attach Link D to Link C's free end
4. Link C becomes parent, Link D becomes child
5. Result: `A → B → C → D` chain ✅

**Scenario 3: Grabbing MP in Long Chain**
```
Link A ----🟣 MP1 ---- Link B ----🟣 MP2 ---- Link C
```

**Process:**
1. Click near MP2
2. `getAllMergedLinks()` finds all links: [A, B, C]
3. Check all connection points in chain
4. Find MP2 (between B and C)
5. Return correct link (B or C) with correct endpoint
6. Dragging works correctly ✅

## Benefits

1. ✅ **No More Detaching**: Links stay connected in 3+ link chains
2. ✅ **Correct MP Detection**: All connection points in chain are detectable
3. ✅ **Proper Chain Extension**: New links attach to correct free TP
4. ✅ **Stable Dragging**: MPs and link surfaces work correctly in long chains
5. ✅ **Handles All Cases**: Parent-to-parent, child-to-child, mixed scenarios

## Testing

### Test 1: 3-Link Chain
1. Create Link A + Link B, merge them
2. Create Link C, connect to Link B's free TP
3. **Expected**: All 3 links stay connected ✅
4. Grab MP1 or MP2
5. **Expected**: MP moves correctly, all links stay connected ✅

### Test 2: 4+ Link Chain
1. Create Link A → Link B → Link C (3-link chain)
2. Create Link D, connect to Link C's free TP
3. **Expected**: All 4 links stay connected ✅
4. Grab any MP
5. **Expected**: MP moves correctly, chain stays intact ✅

### Test 3: Grabbing Link Surface
1. Create 3+ link chain
2. Click on any link in the chain
3. **Expected**: All links in chain highlight ✅
4. Drag the link
5. **Expected**: Entire chain moves together ✅

## Edge Cases Handled

- ✅ **Parent-to-Parent**: Both links are parents → Extend one chain
- ✅ **Child-to-Child**: Both links are children → Find roots, extend appropriately
- ✅ **Parent-to-Child**: Normal case → Works as before
- ✅ **Child-to-Parent**: StretchingLink is child → Extends from its free end
- ✅ **Long Chains**: 3, 4, 5+ links all work correctly
- ✅ **MP Detection**: All MPs in chain are detectable and draggable

## Summary

- **Problem**: 3+ link chains detaching and acting weird
- **Cause**: Merge logic overwriting relationships, incorrect chain extension
- **Solution**: Smart chain extension + enhanced connection point detection
- **Result**: Chains of any length work correctly, MPs and dragging work perfectly ✅

