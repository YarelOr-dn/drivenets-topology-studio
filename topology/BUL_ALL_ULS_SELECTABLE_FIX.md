# Fix: All ULs in BUL Now Selectable - December 4, 2025

## Problem

Only the first and last ULs in a BUL chain could be selected and highlighted. Middle ULs were being skipped.

### User Report
"Only the last 2 ULs in a BUL are being able to selected and highlighted. Fix that so that every UL in a BUL selected will highlight and move the whole link when not connected, and enter link table when connected."

### Example (3-UL BUL)
```
UL1 --MP-1-- UL2 --MP-2-- UL3
✅            ❌            ✅
Can click   SKIPPED      Can click
```

## Root Cause

In the `findObjectAt()` function (line 7190-7192), child links in BUL chains were being skipped:

```javascript
// OLD CODE (WRONG)
if (obj.type === 'unbound' && obj.mergedInto) {
    continue;  // ❌ Skip all child links!
}
```

This meant:
- **UL1** (parent, no mergedInto) → Selectable ✅
- **UL2** (has mergedInto AND mergedWith) → SKIPPED ❌
- **UL3** (has mergedInto, no mergedWith) → Selectable ✅

So in a 3-UL BUL, only UL1 and UL3 were clickable, not UL2.

## The Fix

### Removed the Skip Logic (Line ~7188-7193)

**Before**:
```javascript
if (obj.type === 'unbound' || obj.type === 'link') {
    // Skip child links in BUL chains - they're handled via parent
    if (obj.type === 'unbound' && obj.mergedInto) {
        continue;  // ❌ Skip child links
    }
    // ...
}
```

**After**:
```javascript
if (obj.type === 'unbound' || obj.type === 'link') {
    // CRITICAL FIX: DON'T skip child links - allow clicking ANY UL in a BUL chain
    // When a child link is clicked, we'll select the entire chain in the handler
    // This allows users to click any UL in the BUL, not just first and last
    
    // ... (no continue statement)
}
```

### Why This Works

The selection handler (lines 1608-1616) already has logic to select the entire BUL chain:

```javascript
// ENHANCED: If selecting a merged UL, add ALL links in the merge chain to selection
if (clickedObject.type === 'unbound' && (clickedObject.mergedWith || clickedObject.mergedInto)) {
    const allMergedLinks = this.getAllMergedLinks(clickedObject);
    allMergedLinks.forEach(link => {
        if (!this.selectedObjects.includes(link)) {
            this.selectedObjects.push(link);
        }
    });
}
```

So when ANY UL is clicked (including middle ones), the entire chain gets selected!

## How It Works Now

### Clicking Any UL in BUL

```
BUL: UL1 --MP-1-- UL2 --MP-2-- UL3

Click UL1:
1. findObjectAt() → Returns UL1 ✅
2. Selection handler → Selects ALL (UL1, UL2, UL3) ✅
3. Highlighting → All 3 ULs highlighted ✅

Click UL2 (middle):
1. findObjectAt() → Returns UL2 ✅ (NOW WORKS!)
2. Selection handler → Selects ALL (UL1, UL2, UL3) ✅
3. Highlighting → All 3 ULs highlighted ✅

Click UL3:
1. findObjectAt() → Returns UL3 ✅
2. Selection handler → Selects ALL (UL1, UL2, UL3) ✅
3. Highlighting → All 3 ULs highlighted ✅

All work identically! ✅
```

### Behavior After Selection

**If BUL NOT connected to devices**:
- Can drag entire BUL as one unit
- All ULs move together
- Connection points (MPs) stay synchronized

**If BUL connected to devices**:
- Double-click opens link table
- Shows connection details for entire BUL chain
- Displays TP-1 and TP-2 devices

## Testing

### Test Case 1: 3-UL BUL Selection
1. Create BUL with 3 ULs
2. Click UL1 → All 3 highlighted ✅
3. Click UL2 → All 3 highlighted ✅
4. Click UL3 → All 3 highlighted ✅

### Test Case 2: 5-UL BUL Selection
1. Create BUL with 5 ULs
2. Click each UL in the chain
3. All 5 should highlight when any is clicked ✅

### Test Case 3: Dragging BUL
1. Click any UL in unconnected BUL
2. Drag → Entire BUL moves as rigid unit ✅

### Test Case 4: Link Table
1. Create BUL connected to 2 devices
2. Click any UL in the BUL
3. Double-click → Link table opens ✅
4. Shows TP-1 and TP-2 device info ✅

## Impact

✅ **All ULs selectable**: Click any UL in the chain
✅ **Entire chain highlights**: Visual feedback for whole BUL
✅ **Consistent behavior**: All ULs work the same way
✅ **Intuitive UX**: Click anywhere on BUL to select it

## Technical Details

### Selection Priority Order

The `findObjectAt()` function uses priority:
1. **Devices** (highest priority)
2. **Text objects**
3. **Links and unbound links** (lowest priority)
   - Now includes ALL ULs (no skipping)

### Distance Calculation

For BUL chains, the distance calculation includes:
- Parent link distance
- ALL child link distances (recursive)
- Returns whichever UL is closest to click point

### Highlighting

The `drawUnboundLink()` function checks:
```javascript
let isSelected = this.selectedObject === link || this.selectedObjects.includes(link);
```

Since `selectedObjects` contains ALL links in the chain (via `getAllMergedLinks()`), all links get the selection highlight!

## Related Features

- BUL multi-select movement
- BUL drag as rigid unit
- Link table for BUL chains
- MP highlighting and numbering

## Date

December 4, 2025

## Status

✅ **Complete** - All ULs in BUL are now fully selectable and interactive





