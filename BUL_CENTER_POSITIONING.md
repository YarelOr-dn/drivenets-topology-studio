# Fix: BUL Connections Now at Dead Center - December 4, 2025

## Problem

BUL (Bundled Unbound Link) connections to devices were being positioned with offsets like regular links, instead of at the dead center.

### User Request
"Make BUL UI when connected to be at the dead center like normal link connection please"

## Root Cause

When a BUL has both endpoints connected to devices, the positioning code calculated an offset based on `linkIndex` to space multiple links apart. This worked for regular Quick Links (QLs) but wasn't desired for BULs.

### The Logic (Line ~12096-12103)

```javascript
const linkIndex = this.calculateLinkIndex(obj);
if (linkIndex > 0) {
    const magnitude = Math.ceil(linkIndex / 2) * 20;
    const direction = (linkIndex % 2 === 1) ? 1 : -1;
    offsetAmount = magnitude * direction;
}
```

**Result**:
- First link (QL or BUL): Center (linkIndex = 0)
- Second link: Right offset (+20px)
- Third link: Left offset (-20px)
- Etc.

**Problem**: BULs were being treated like QLs and getting offsets.

## The Fix

### Force BULs to Always Use Center Position

Changed line ~12096-12103:

**Before**:
```javascript
const linkIndex = this.calculateLinkIndex(obj);
if (linkIndex > 0) {
    // Apply offset based on index
}
```

**After**:
```javascript
// CRITICAL FIX: BULs always go to center (linkIndex = 0), only QLs use offset
const isBUL = obj.mergedWith || obj.mergedInto;
const linkIndex = isBUL ? 0 : this.calculateLinkIndex(obj); // BULs always center

if (linkIndex > 0) {
    // Apply offset (only for QLs now, BULs always 0)
}
```

## How It Works Now

### Link Positioning Logic

**Quick Links (QLs)**:
- First QL: Center (linkIndex = 0)
- Second QL: Right offset (+20px)
- Third QL: Left offset (-20px)
- Pattern continues...

**BULs (Bundled Unbound Links)**:
- **Always**: Dead center (linkIndex forced to 0)
- **Never**: Offset, regardless of how many links exist

### Visual Example

**Before Fix**:
```
Device1              Device2
   |                    |
   |---- QL1 --------   | (center)
   |                    |
   |---- BUL ----/      | (offset right - WRONG)
   |            /       |
   |           /        |
```

**After Fix**:
```
Device1              Device2
   |                    |
   |---- QL1 --------   | (center)
   |                    |
   |---- BUL --------   | (center - CORRECT!)
   |                    |
```

### Multiple Links Between Same Devices

```
Scenario: 2 QLs + 1 BUL between Device1 and Device2

Before:
- QL1: Center
- QL2: Right offset
- BUL: Left offset ❌

After:
- BUL: Dead center ✅
- QL1: Right offset
- QL2: Left offset

BUL gets priority at center!
```

## Benefits

✅ **Clean Appearance**: BULs at center look cleaner
✅ **Predictable**: BULs always center, regardless of other links
✅ **Professional**: Matches normal link behavior
✅ **Consistent**: All BULs positioned the same way

## Implementation Details

### Detection

```javascript
const isBUL = obj.mergedWith || obj.mergedInto;
```

**True if**:
- Link has `mergedWith` (parent in BUL)
- Link has `mergedInto` (child in BUL)

**False if**:
- Standalone UL (not merged)
- Quick Link (regular link)

### Offset Calculation

```javascript
linkIndex = isBUL ? 0 : this.calculateLinkIndex(obj);

if (linkIndex > 0) {
    // This only executes for QLs now
    // BULs have linkIndex = 0, so skip offset
}
```

**Result**: 
- BULs: `linkIndex = 0` → `offsetAmount = 0` → Center position
- QLs: `linkIndex = calculated` → Offset applied

## Testing

### Test Case 1: Single BUL
1. Create BUL (2 ULs connected)
2. Attach both TPs to devices
3. Observe: BUL at **dead center** ✅

### Test Case 2: BUL + QL
1. Create QL between Device1 and Device2
2. Create BUL between same devices
3. Observe:
   - BUL: **Dead center** ✅
   - QL: Offset to side ✅

### Test Case 3: Multiple Links
1. Create 2 QLs + 1 BUL between same devices
2. Observe:
   - BUL: **Dead center** ✅
   - QLs: Offset on both sides ✅

## Code Location

**File**: `topology.js`
**Line**: ~12096-12103
**Function**: Part of `draw()` method, UL position update section

## Related Features

- Link offset calculation
- BUL chain positioning
- Device attachment
- Link table display

## Impact

**Low Risk**: 
- Only affects BUL positioning when both ends connected
- Does not affect BUL dragging, MPs, or TPs
- Does not affect QL positioning
- Clean, simple logic

## Date

December 4, 2025

## Status

✅ **Complete** - BULs now always position at dead center when connected to devices





