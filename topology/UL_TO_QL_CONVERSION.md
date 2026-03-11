# Standalone UL → QL Conversion - December 4, 2025

## Feature

Standalone ULs (Unbound Links) now automatically convert to QLs (Quick Links) when both ends are attached to devices, making them connect exactly like normal links.

### User Request
"Make a standalone UL stick to devices and after sticking to devices at both sides make it connect the same exact way as a QL/normal link"

## Implementation

### Auto-Conversion Logic (Line ~5476-5489)

When a UL's second endpoint attaches to a device:
1. Check if it's standalone (not part of BUL)
2. Check if both ends now attached
3. If yes → **Convert to QL**

**Code**:
```javascript
// CRITICAL: Convert standalone UL to QL when both ends are attached to devices
if (this.stretchingLink.device1 && this.stretchingLink.device2 && 
    !this.stretchingLink.mergedWith && !this.stretchingLink.mergedInto) {
    // Standalone UL with both ends attached → Convert to QL
    this.stretchingLink.type = 'link';
    if (this.stretchingLink.originType === 'UL') {
        this.stretchingLink.originType = 'QL'; // Mark as converted
    }
    
    this.debugger.logSuccess(`🔄 Standalone UL converted to QL`);
}
```

### When Conversion Happens

**Scenario 1: Create UL, attach both ends**
```
Step 1: Create UL (double-tap canvas)
   type: 'unbound'
   device1: null
   device2: null
   
Step 2: Drag start to Device1
   type: 'unbound'
   device1: Device1
   device2: null
   
Step 3: Drag end to Device2
   type: 'link' ✅ (AUTO-CONVERTED!)
   device1: Device1
   device2: Device2
   
Now behaves EXACTLY like QL!
```

**Scenario 2: UL in BUL - NO conversion**
```
BUL: UL1 --MP-- UL2
     device1  device2
     
Even with both ends attached:
   type: 'unbound' (stays UL)
   
Reason: Part of BUL, not standalone
```

### What Doesn't Convert

ULs that are part of a BUL chain stay as ULs:
- ❌ UL with `mergedWith` (parent in BUL)
- ❌ UL with `mergedInto` (child in BUL)
- ✅ Only standalone ULs convert

## Benefits

### Exact QL Behavior

After conversion, the UL becomes a QL and:
- ✅ Renders using `drawLink()` (not `drawUnboundLink()`)
- ✅ Uses QL positioning logic
- ✅ Uses QL offset calculation
- ✅ Shows QL-style connections
- ✅ No TPs displayed (QLs don't have TPs)
- ✅ Matches QL appearance 100%

### Automatic & Seamless

- User creates UL (for flexibility)
- User attaches both ends
- System automatically converts to QL
- User gets QL behavior without thinking about it

### Visual Result

**Before Conversion (UL)**:
```
Device1 ⚪━━━━━⚪ Device2
        TP    TP
```

**After Conversion (QL)**:
```
Device1 ━━━━━━━━ Device2
     (No TPs, just connection)
```

Looks and behaves exactly like a Quick Link created with link mode!

## Technical Details

### Type Change
```javascript
// Before
link.type = 'unbound'
link.originType = 'UL'

// After
link.type = 'link'
link.originType = 'QL' // or keeps 'UL' to remember origin
```

### Drawing Dispatch

```javascript
drawLink(link) {
    if (link.type === 'unbound') {
        this.drawUnboundLink(link);  // BUL rendering
        return;
    }
    // QL rendering (converted ULs use this!)
    // ... standard link drawing code
}
```

Converted ULs skip `drawUnboundLink()` and use standard link rendering!

### Positioning

After conversion, uses QL positioning:
- Same offset logic
- Same curve handling
- Same device edge attachment
- Same multiple-link spacing

## Testing

### Test Case 1: Single UL Both Ends Attached
1. Double-tap canvas → Create UL
2. Drag start to Device1
3. Observe: Still UL (one TP free)
4. Drag end to Device2
5. **Observe**: Auto-converts to QL ✅
6. **Result**: Looks exactly like QL ✅

### Test Case 2: UL in BUL - No Conversion
1. Create 2-UL BUL
2. Attach both TPs to devices
3. **Observe**: Stays as UL (part of BUL) ✅
4. **Result**: Keeps BUL behavior ✅

### Test Case 3: Multiple Links Between Same Devices
1. Create QL between Device1-Device2
2. Create UL, attach both ends to same devices
3. **Observe**: UL converts to QL ✅
4. **Result**: Both QLs, proper offset spacing ✅

## Workflow Examples

### Creating UL-based Connection
```
User creates UL (for flexibility):
1. Double-tap canvas
2. Drag to Device1 (attaches)
3. Drag to Device2 (attaches + AUTO-CONVERTS)
4. Result: QL connection ✅
```

### Creating BUL
```
User creates UL for BUL:
1. Double-tap canvas
2. Drag to Device1 (attaches)
3. Create another UL
4. Connect UL1-TP to UL2-TP
5. Result: BUL (stays as ULs) ✅
6. Later: Attach second TP to device
7. Result: Still BUL (no conversion) ✅
```

## Why This Works

### The Key Check
```javascript
!this.stretchingLink.mergedWith && !this.stretchingLink.mergedInto
```

This ensures:
- ✅ Standalone ULs convert
- ❌ BUL parents don't convert (have mergedWith)
- ❌ BUL children don't convert (have mergedInto)

### Perfect Behavior

**Standalone UL** + **Both Ends Attached** = **QL**
- Simple, predictable, intuitive

**UL in BUL** + **Ends Attached** = **Still UL**
- Preserves BUL structure
- Keeps MPs functional

## Code Location

**File**: `topology.js`
**Line**: ~5476-5489
**Function**: Part of `handleMouseUp()`, device attachment section
**Triggers**: When second endpoint attaches to device

## Related Features

- UL creation (double-tap)
- Device attachment (magnetic snap)
- BUL creation (TP merging)
- QL creation (link mode)

## Benefits

✅ **User-Friendly**: Works automatically
✅ **Exact Match**: Behaves identically to QL
✅ **Smart**: Only converts when appropriate
✅ **Preserves BULs**: Doesn't break merge chains
✅ **Clean**: No manual conversion needed

## Date

December 4, 2025

## Status

✅ **Complete** - Standalone ULs auto-convert to QLs when both ends attached to devices





