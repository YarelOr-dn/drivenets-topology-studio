# MPs Cannot Be Merge Targets - Confirmed Behavior

## Rule: Once MP is Created, No Connection is Allowed

**Moving Points (MPs)** are connection points between merged ULs. Once created, they **cannot** be used as merge targets for other ULs.

## What This Means

### ✅ Allowed
- **TP → TP** merging (creates new MP)
- **TP → Device** attachment
- **MP dragging** (to adjust routing)

### 🚫 Blocked
- **TP → MP** merging (MPs are not merge targets)
- **MP → MP** merging (MPs are for routing only)
- **MP → Device** attachment (MPs stay as MPs)

## Visual Guide

```
Scenario: UL3 trying to connect to existing MP

UL1 ----🟣 MP ----🔘 UL2
        ↑
        🔘 UL3 tries to merge here
        
Result: ❌ BLOCKED
Reason: MPs are not merge targets
```

## Why This Rule?

1. **Clarity**: MPs are for routing, not for creating multi-way merges
2. **Predictability**: Connection points have one purpose - adjusting link shape
3. **Simplicity**: Only TPs can merge, keeping the mental model simple
4. **Visual distinction**: Purple = routing only, Gray = can merge

## How It Works Technically

### Detection Logic (handleMouseUp - Lines 3347-3415)

The code checks if an endpoint is a connection point before allowing it as a merge target:

```javascript
// Check if endpoint is a connection point
let startIsConnectionPoint = false;

if (obj.connectedTo && obj.connectedTo.thisEndpoint === 'start') {
    startIsConnectionPoint = true;
} else if (obj.mergedWith && obj.mergedWith.parentFreeEnd !== 'start') {
    startIsConnectionPoint = true;
} else if (obj.mergedInto) {
    const parentLink = this.objects.find(o => o.id === obj.mergedInto.parentId);
    if (parentLink && parentLink.mergedWith) {
        const childFreeEnd = parentLink.mergedWith.childFreeEnd;
        startIsConnectionPoint = (childFreeEnd !== 'start');
    }
}

// Only allow merging if NOT a connection point
if (!obj.device1 && !startIsConnectionPoint) {
    // This endpoint can be a merge target ✅
}
```

### Three Types of Endpoints

| Type | Color | Can Merge With? | Can Drag? | Purpose |
|------|-------|-----------------|-----------|---------|
| **TP (Free)** | Gray 🔘 | ✅ Yes (TP or Device) | ✅ Yes | Create new merges |
| **MP (Connection)** | Purple 🟣 | 🚫 No | ✅ Yes | Adjust routing |
| **Device-attached** | Green 🟢 | 🚫 No | 🚫 No | Fixed to device |

## Examples

### Example 1: Cannot Merge at MP

```
Initial state:
UL1 ----🟣---- UL2
       MP

Try to merge UL3 at MP:
UL1 ----🟣---- UL2
        ↑
       🔘 UL3 (trying to connect)
       
Result: ❌ No merge happens
Why: MPs are not merge targets
```

### Example 2: Use TP Instead

```
Correct way to extend chain:
UL1 ----🟣---- UL2 ----🔘 TP (free endpoint)
                        ↑
                       🔘 UL3 connects here
                       
Result: ✅ New merge created
UL1 ----🟣---- UL2 ----🟣---- UL3
              MP1         MP2
```

### Example 3: Creating Star Topology

```
Wrong approach (trying to merge at MP):
        🔘 UL1
         ↓ (trying to connect to MP)
Device--🟣--🔘 UL2
        MP

❌ Won't work - MP is not a merge target

Correct approach (attach to device):
        🔘 UL1
         ↓ (attach to device)
Device--🟢--🔘 UL2
     Green attachment points
     
✅ Works - device attachments are separate from MPs
```

## User Feedback

When attempting to merge at an MP:
- **No visual snap** (MP doesn't highlight)
- **No merge happens** (TPs only merge with other TPs)
- **Cursor remains normal** (no crosshair)

## Benefits of This Rule

1. ✅ **Prevents Confusion**: Clear distinction between TPs (mergeable) and MPs (routing)
2. ✅ **Consistent Behavior**: MPs always behave the same way
3. ✅ **Visual Clarity**: Purple = not for merging
4. ✅ **Predictable**: Users learn quickly that only gray TPs can merge

## Summary

- **MPs (Purple 🟣)** = Routing control points, **NOT** merge targets
- **TPs (Gray 🔘)** = Free endpoints, **CAN** merge with other TPs
- **Once MP is created** = That location is **permanently** a routing point
- **To extend chain** = Use the **free TPs**, not the MPs

## Implementation Status

✅ **Fully Implemented**
- MPs are correctly excluded from merge target detection
- Code at lines 3354-3368 and 3385-3399 checks and skips MPs
- No code changes needed - already working as designed

## Testing Confirmation

To verify this works:
1. Create UL1 and UL2, merge them (MP appears)
2. Create UL3
3. Try to drag UL3's TP to the purple MP
4. **Expected**: No merge happens, no snap, MP stays purple
5. **Try instead**: Drag UL3's TP to UL2's free TP (gray)
6. **Expected**: Merge happens! New MP created between UL2 and UL3

