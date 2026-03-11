# CRITICAL ROOT CAUSE: getAllMergedLinks() Wrong Order

## The Root Problem Found!

From debug logs line 121:
```
Chain order: ["unbound_0", "unbound_1", "unbound_2"]  ✅ Correct
mpData order: [unbound_1, unbound_2, unbound_0]  ❌ WRONG!
```

The `mpData` is in the wrong order because `getAllMergedLinks()` was returning links in **random Set order**, not chain order!

## The Bug

### Old Code (Lines 7567-7612)
```javascript
getAllMergedLinks(link) {
    const mergedSet = new Set();  // ❌ Sets don't preserve insertion order reliably
    // ... complex traversal that adds to Set
    return Array.from(mergedSet);  // ❌ Order unpredictable!
}
```

**Problem**: Using a `Set` meant the order was based on Set iteration order, which doesn't match chain structure.

## The Fix

### New Code - Ordered Traversal
```javascript
getAllMergedLinks(link) {
    // Find head first
    let head = link;
    while (head.mergedInto) {
        head = this.objects.find(o => o.id === head.mergedInto.parentId);
    }
    
    // Traverse head to tail in order
    const orderedLinks = [head];
    let current = head;
    
    while (current.mergedWith) {
        const child = this.objects.find(o => o.id === current.mergedWith.linkId);
        orderedLinks.push(child);
        current = child;
    }
    
    return orderedLinks;  // ✅ Always in chain order!
}
```

## Why This Fixes Everything

When `getAllMergedLinks()` returns correct order:
- ✅ MP numbers assigned correctly (MP-1, MP-2, MP-3...)
- ✅ mpData array in correct order
- ✅ MP detection finds right MP
- ✅ MP dragging uses correct partner
- ✅ Everything works!

## Impact on UL-2

**Before**: Chain order random → MP-1 data might be after MP-2 → Wrong MP grabbed
**After**: Chain order guaranteed → MP-1 always first → Correct MP grabbed

## Date

December 4, 2025



