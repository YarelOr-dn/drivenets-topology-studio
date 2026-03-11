# CRITICAL FIX: UL-2 Append Endpoint Calculation

## Problem Found

When appending UL-3 to UL-2 (tail), the code had a conditional check that SKIPPED the targetEndpoint recalculation if `parentLink` already equaled `chainTail`.

### The Broken Logic (Line 4940)

```javascript
if (parentLink.id !== chainTail.id) {
    parentLink = chainTail;
    // Calculate targetEndpoint...
}
// If parentLink.id === chainTail.id, we SKIP this block!
// targetEndpoint never gets recalculated!
```

**Result**: If we detected UL-2 directly (so `parentLink.id === chainTail.id`), we used the initially detected `nearbyULEndpointType` which might be wrong, instead of calculating the actual free end from the chain structure.

## The Fix

**Removed the conditional** - ALWAYS recalculate targetEndpoint for tail:

```javascript
// CRITICAL FIX: Always recalculate targetEndpoint for tail
parentLink = chainTail; // Unconditional assignment

// ALWAYS calculate the tail's free end
if (chainTail.mergedInto) {
    const tailParent = this.objects.find(...);
    if (tailParent?.mergedWith) {
        const tailFreeEnd = tailParent.mergedWith.childFreeEnd;
        targetEndpoint = tailFreeEnd;
    }
}
```

Now the targetEndpoint is **always** calculated correctly from the chain structure, not from initial detection.

## Why This Fixes MP-1

When UL-3 connects to UL-2:
- ✅ UL-2's free end correctly identified
- ✅ UL-2's mergedWith created with correct endpoints
- ✅ UL-2 becomes middle link (has both mergedInto and mergedWith)
- ✅ MP-1 data stays intact (UL-1 ↔ UL-2)
- ✅ MP-2 data correct (UL-2 ↔ UL-3)
- ✅ Both MPs work!

## Date

December 4, 2025



