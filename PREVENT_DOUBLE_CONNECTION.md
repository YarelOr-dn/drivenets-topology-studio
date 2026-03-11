# Prevent Double Connection Between Links Sharing an MP

## Problem

When two links already share an MP (Moving Point / connection point), their free TPs (Termination Points) could still connect to each other, creating a redundant second connection.

**Example of the bug:**
```
Link A ----🟣 MP ---- Link B
   🔘 TP              🔘 TP
    ↑                 ↑
    └─────────────────┘
    (Could connect - WRONG!)
```

## Solution

Added a check to prevent links that already share an MP from connecting their free TPs.

**Now blocked:**
```
Link A ----🟣 MP ---- Link B
   🔘 TP              🔘 TP
    ↑                 ↑
    └─────────────────┘
    (Connection BLOCKED ✅)
```

## Implementation

### New Helper Function

**`linksAlreadyShareMP(link1, link2)`** - Lines 5047-5075

Checks if two links already share an MP by:
1. **Direct relationship**: One is parent/child of the other
2. **Indirect relationship**: Both are in the same merge chain

```javascript
linksAlreadyShareMP(link1, link2) {
    // Direct parent-child relationship
    if (link1.mergedWith && link1.mergedWith.linkId === link2.id) return true;
    if (link2.mergedWith && link2.mergedWith.linkId === link1.id) return true;
    if (link1.mergedInto && link1.mergedInto.parentId === link2.id) return true;
    if (link2.mergedInto && link2.mergedInto.parentId === link1.id) return true;
    
    // Check if they're in the same merge chain
    const link1Chain = this.getAllMergedLinks(link1);
    const link2Chain = this.getAllMergedLinks(link2);
    
    // If they share any link in their chains, they're already connected
    for (const chainLink1 of link1Chain) {
        for (const chainLink2 of link2Chain) {
            if (chainLink1.id === chainLink2.id) {
                return true; // Same merge chain
            }
        }
    }
    
    return false; // No shared MP
}
```

### Merge Prevention

**In `handleMouseUp()`** - Lines 3422-3430

Before allowing a merge, check if links already share an MP:

```javascript
if (nearbyULLink && nearbyULEndpoint) {
    // CRITICAL: Check if these two links already share an MP
    const alreadyShareMP = this.linksAlreadyShareMP(this.stretchingLink, nearbyULLink);
    
    if (alreadyShareMP) {
        // These links already have an MP together - don't allow another connection
        if (this.debugger) {
            this.debugger.logInfo(`🚫 Cannot merge: Links already share an MP`);
        }
        return; // Block the merge
    }
    
    // Proceed with merge...
}
```

## Scenarios Handled

### Scenario 1: Direct Parent-Child
```
Link A (parent) ----🟣 MP ---- Link B (child)
```
- Link A has `mergedWith.linkId = Link B.id`
- Link B has `mergedInto.parentId = Link A.id`
- ✅ **Blocked**: Can't connect their free TPs

### Scenario 2: Same Merge Chain
```
Link A ----🟣 MP1 ---- Link B ----🟣 MP2 ---- Link C
```
- All three links are in the same chain
- ✅ **Blocked**: Link A's free TP can't connect to Link C's free TP

### Scenario 3: Different Chains
```
Chain 1: Link A ----🟣 MP ---- Link B
Chain 2: Link C ----🟣 MP ---- Link D
```
- Link A and Link C are in different chains
- ✅ **Allowed**: Can connect Link A's TP to Link C's TP

## Visual Examples

### Before Fix ❌
```
Link A ----🟣---- Link B
  🔘              🔘
   └──────────────┘
   (Could create second connection - BAD!)
```

### After Fix ✅
```
Link A ----🟣---- Link B
  🔘              🔘
   └──────────────┘
   (Blocked - already connected via MP!)
```

### Allowed Case ✅
```
Link A ----🟣---- Link B    Link C ----🟣---- Link D
  🔘              🔘          🔘              🔘
   └──────────────┘            └──────────────┘
   (Different chains - CAN connect!)
```

## Benefits

1. ✅ **Prevents Redundancy**: No duplicate connections
2. ✅ **Cleaner Topologies**: One connection per link pair
3. ✅ **Logical Consistency**: If already connected, can't connect again
4. ✅ **Works with Chains**: Handles long merge chains correctly

## Testing

### Test 1: Direct Merge Prevention
1. Create Link A and Link B
2. Merge them (MP appears)
3. Try to connect Link A's free TP to Link B's free TP
4. **Expected**: ❌ Blocked (already share MP)

### Test 2: Chain Merge Prevention
1. Create Link A → Link B → Link C (chain)
2. Try to connect Link A's free TP to Link C's free TP
3. **Expected**: ❌ Blocked (same chain)

### Test 3: Different Chains Allowed
1. Create Chain 1: Link A → Link B
2. Create Chain 2: Link C → Link D
3. Try to connect Link A's TP to Link C's TP
4. **Expected**: ✅ Allowed (different chains)

## Technical Details

### Detection Logic

1. **Direct Check**: O(1) - Check parent/child relationships
2. **Chain Check**: O(n²) - Compare merge chains (only if direct check fails)
3. **Performance**: Fast for most cases, efficient chain comparison

### Edge Cases Handled

- ✅ Links that are parent/child
- ✅ Links in same merge chain (3+ links)
- ✅ Links with multiple MPs in chain
- ✅ Links that are both parents/children of others

## Files Modified

- **topology.js** - Lines 3422-3430 (merge prevention), Lines 5047-5075 (helper function)

## Summary

- **Problem**: Links sharing an MP could create redundant connections
- **Solution**: Check before merging if links already share an MP
- **Result**: Cleaner topologies, no duplicate connections ✅
- **Works with**: All link types, long chains, complex merges

