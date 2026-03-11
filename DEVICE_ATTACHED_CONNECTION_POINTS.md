# Device-Attached Connection Points - Updated Behavior

## Overview

When merged ULs (Unbound Links) connect to devices, the connection points at the device locations now **disappear** and are **no longer available for merging** with other ULs. This prevents multiple ULs from merging at the same device attachment point and ensures cleaner topology layouts.

## New Behavior

### ✅ What Changed

1. **Connection Points on Devices are Hidden** 🚫🟣
   - When a merged UL's connection point attaches to a device, the purple connection point **disappears**
   - The endpoint becomes a regular green device attachment point
   - The connection point is no longer visible or draggable

2. **No UL Merging at Device-Attached Points** 🔒
   - Other ULs cannot merge with connection points that are on devices
   - When you drag a UL endpoint near a device-attached connection point, it will **attach directly to the device** instead
   - This prevents unintended multi-way merges at device locations

3. **Device Priority** 🎯
   - Devices take priority over connection points when both are at the same location
   - ULs will always prefer attaching to the device rather than merging with an already-attached connection point

## How It Works

### Before Device Attachment
```
UL1 ----🟣---- UL2       (Purple connection point is movable)
```

### After Device Attachment
```
UL1 ----🟢 Device 🟢---- UL2    (Green device attachments, no purple connection point)
```

### When Another UL Approaches
```
UL1 ----🟢 Device 🟢---- UL2
              ↑
            UL3 (Will attach to Device, NOT merge with connection point)
```

## Technical Implementation

### Modified Functions

1. **`drawUnboundLink()` - Lines 8833-8889 & 8929-8985**
   - Added `connectionPointOnDevice` check before drawing purple connection points
   - Checks both parent and child links for device attachment
   - Only draws connection point if NOT attached to a device

2. **`findUnboundLinkEndpoint()` - Lines 7525-7583**
   - Enhanced to skip connection points that are on devices
   - Checks `isOnDevice` flag before returning connection point detection
   - Allows regular endpoint detection to proceed if connection point is on device

3. **`handleMouseUp()` - Lines 3353-3379**
   - Modified UL endpoint snapping to skip device-attached endpoints
   - Checks `!obj.device1` and `!obj.device2` before considering endpoints for merging
   - Ensures ULs only merge at free (non-device-attached) endpoints

### Logic Flow

```javascript
// For each endpoint being checked for merging:
if (endpoint is part of merged UL) {
    const connectedEndpoint = /* determine which endpoint is connected */;
    const isOnDevice = (endpoint attached to device);
    
    if (isOnDevice) {
        // Don't draw purple connection point
        // Don't allow merging
        // Let normal device attachment happen instead
    } else {
        // Draw purple connection point
        // Allow merging with other ULs
        // Allow dragging to move connection point
    }
}
```

## Usage Examples

### Example 1: Creating a Star Topology
```
Before:
  UL1 ----🟣---- UL2
  UL3 ----🟣---- UL4

After attaching to Device:
  UL1 ----🟢
            Device (center)
  UL3 ----🟢     🟢---- UL2
                 🟢---- UL4
```

### Example 2: Preventing Unwanted Merges
```
Problem (Old Behavior):
  UL1 ----🟣 Device 🟣---- UL2
           ↓
        UL3 merges with connection point (messy)

Solution (New Behavior):
  UL1 ----🟢 Device 🟢---- UL2
           🟢
           UL3 (attaches to device cleanly)
```

## Benefits

1. **✅ Cleaner Topologies**: Multiple ULs can connect to the same device without creating complex merge chains

2. **✅ Intuitive Behavior**: Device attachments behave consistently - once attached, they're no longer merge points

3. **✅ Visual Clarity**: 
   - Purple 🟣 = Movable connection point (free in space)
   - Green 🟢 = Device attachment (fixed to device)

4. **✅ Prevents Confusion**: Users won't accidentally merge ULs when they intended to attach to a device

5. **✅ Flexible Layouts**: Connection points remain movable until attached to devices, giving maximum flexibility

## User Workflow

### Creating Merged ULs with Device Connections

1. **Create first UL** - Double-tap or Cmd+L
2. **Create second UL** - Another double-tap or Cmd+L
3. **Merge them** - Drag one endpoint near the other (🟣 purple connection point appears)
4. **Move connection point** (optional) - Drag the purple connection point to adjust routing
5. **Attach to device** - Drag the connection point to a device
6. **Result**: Purple connection point disappears, becomes green device attachment
7. **Add more ULs** - New ULs attach directly to the device, don't merge with connection point

### Important Notes

- ⚠️ Once a connection point attaches to a device, it **cannot** be used as a merge point
- ✅ You can still move the connection point **before** it attaches to a device
- ✅ Other ULs can still attach to the same device (they just won't merge with the connection point)
- ✅ The merge relationship between the two original ULs is maintained

## Edge Cases Handled

1. **Connection point moves onto device**: Purple → Green transition happens automatically
2. **Multiple ULs at same device**: Each attaches independently, no unwanted merges
3. **Dragging connection point away from device**: Would need to detach device connection first (future enhancement)
4. **Deleting one merged UL**: Other UL remains intact with device attachment

## Comparison: Before vs After

| Scenario | Old Behavior | New Behavior |
|----------|-------------|--------------|
| Merged UL connects to device | Purple connection point remains visible | Connection point disappears (becomes green) |
| Another UL dragged to same location | Merges with connection point | Attaches to device directly |
| Connection point on device | Draggable, visible, sticky | Not draggable, hidden, non-sticky |
| Visual indicator | Purple (misleading) | Green (correct - shows device attachment) |

## Future Enhancements

Possible improvements:
- [ ] Allow "unmerging" ULs by dragging connection point far from device
- [ ] Show tooltip explaining why connection point disappeared
- [ ] Animate the purple → green transition
- [ ] Allow re-enabling connection point by detaching from device
- [ ] Support multi-point merges (more than 2 ULs) at free space (not on devices)

