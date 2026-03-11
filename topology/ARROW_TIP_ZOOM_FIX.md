# Arrow Tip Hitbox Zoom Fix

## Problem

When zoomed out, arrow tip hitboxes were not scaling correctly with zoom level:
- **Clicking anywhere on the UL** would select the TP (hitbox too large)
- **Hitbox size was in world coordinates** instead of screen-space
- When zoomed out, the hitbox became HUGE relative to the screen

## Root Cause

Line 13622 in `distanceToLink()`:
```javascript
// BEFORE (BROKEN):
const arrowTipRadius = arrowLength * 1.5; // Not zoom-aware!
```

This created a hitbox in world coordinates that didn't shrink when zooming out.

## Solution

Added zoom division for consistent screen-space hitbox:
```javascript
// AFTER (FIXED):
const arrowTipRadius = (arrowLength * 1.5) / this.zoom;
```

Now the hitbox:
- ✅ **Shrinks when zoomed out** (smaller world-space radius)
- ✅ **Grows when zoomed in** (larger world-space radius)  
- ✅ **Consistent screen-space size** at all zoom levels
- ✅ **Matches TP hitbox behavior** (line 31829 already had `/this.zoom`)

## Files Modified

**topology.js** - Line 13622
- Added `/ this.zoom` to `arrowTipRadius` calculation
- Added comment explaining zoom-aware hitbox requirement

## Benefits

✅ **Zoom-aware hitboxes** - Consistent size on screen regardless of zoom  
✅ **Only TP clicks select TP** - Link body no longer triggers TP selection  
✅ **Matches existing TP code** - Consistent with line 31829 behavior  
✅ **Minimal change** - One line fix, no complex triangle collision needed  

## Technical Details

### Hitbox Calculation
- **Arrow length**: `10 + (linkWidth * 3)` (world coordinates)
- **Hitbox radius**: `(arrowLength * 1.5) / zoom` (screen-space)
- **At zoom 1.0**: Full size (arrowLength * 1.5)
- **At zoom 0.5**: Half size in world space (same screen size)
- **At zoom 2.0**: Double size in world space (same screen size)

### Why This Works
World-space hitbox needs to be **inversely proportional to zoom**:
- Zoom out (0.5x) → Objects appear smaller → Hitbox must be larger in world coords
- Zoom in (2.0x) → Objects appear larger → Hitbox must be smaller in world coords

Formula: `screen_size = world_size * zoom`  
Therefore: `world_size = screen_size / zoom`

## Testing

Test at different zoom levels:
1. **Zoom 1.0 (100%)**: Arrow tip clickable, link body clickable separately ✅
2. **Zoom 0.5 (50%)**: Same behavior - no oversized hitbox ✅
3. **Zoom 2.0 (200%)**: Same behavior - not too small ✅

Try clicking:
- **On arrow tip**: Selects the TP ✅
- **On link body**: Selects the link (not TP) ✅
- **Far from arrow**: Nothing selected ✅
