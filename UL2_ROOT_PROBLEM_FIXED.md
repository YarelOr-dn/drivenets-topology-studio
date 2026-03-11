# ROOT PROBLEM FIXED: UL-2 Connection Endpoint Detection

## The Root Cause - TWO Issues

### Issue 1: Conditional targetEndpoint Update (Line 4940)
**Problem**: Only updated targetEndpoint if `parentLink.id !== chainTail.id`
**Fix**: Removed conditional - ALWAYS recalculate for tail

### Issue 2: Wrong Endpoint Detection Logic (Line 5117)  
**Problem**: Used `nearbyULEndpointType` even when parentLink has `mergedInto` (is part of chain)
**Fix**: Only use detected endpoint if parent is NOT in a chain

## The Complete Fix

### Before (Broken)
```javascript
// Step 2: Append logic
if (parentLink.id !== chainTail.id) {
    parentLink = chainTail;
    targetEndpoint = tailFreeEnd; // Only calculated here!
}
// If already equals, targetEndpoint NOT updated! ❌

// Step 3: Endpoint detection
else if (isParentOriginalTarget) {
    // Uses detected endpoint even for tail in chain! ❌
    parentConnectingEnd = nearbyULEndpointType;
}
```

### After (Fixed)
```javascript
// Step 2: Append logic  
parentLink = chainTail; // Unconditional
if (chainTail.mergedInto) {
    const tailFreeEnd = tailParent.mergedWith.childFreeEnd;
    targetEndpoint = tailFreeEnd; // ALWAYS calculated! ✅
}

// Step 3: Endpoint detection
else if (isParentOriginalTarget && !parentLink.mergedInto) {
    // Only use detected if NOT in chain! ✅
    parentConnectingEnd = nearbyULEndpointType;
} else {
    // For chain members, calculate from structure ✅
    if (parentLink.mergedInto) {
        const tailFreeEnd = chainParent.mergedWith.childFreeEnd;
        parentConnectingEnd = tailFreeEnd;
    }
}
```

## Why This Broke MPs

### Scenario: UL-1 --MP-1-- UL-2, then connect UL-3 to UL-2

**With Bug**:
1. Detect UL-2 directly (nearbyULLink = UL-2)
2. `parentLink.id === chainTail.id` → TRUE
3. Skip targetEndpoint recalculation
4. Use wrong nearbyULEndpointType in Step 3
5. UL-2's mergedWith created with WRONG endpoints
6. MP-1 data inconsistent (UL-2's endpoints wrong)
7. MP-1 breaks! ❌

**After Fix**:
1. Detect UL-2 directly
2. ALWAYS recalculate targetEndpoint from chain
3. Check if parentLink has mergedInto before using detected endpoint
4. Use chain structure to get correct free end
5. UL-2's mergedWith created with CORRECT endpoints
6. MP-1 data stays intact
7. MP-1 works! ✅

## Result

✅ **MP-1 (UL-1 ↔ UL-2)**: Works correctly after UL-3 connects
✅ **MP-2 (UL-2 ↔ UL-3)**: Works correctly
✅ **All MPs functional**: Regardless of connection order
✅ **UL-2 integrity**: Connections don't corrupt each other

## Date

December 4, 2025



