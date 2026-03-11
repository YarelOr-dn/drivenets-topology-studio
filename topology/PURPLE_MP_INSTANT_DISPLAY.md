# Fix: Purple MP Shows Immediately on TP Merge - December 4, 2025

## Problem

When releasing a TP to merge with another TP, the animation showed a **green dot** instead of immediately showing the **purple MP (Moving Point)**.

### User Report
"The TPs merging animation should end when MP is seen (purple dot like now). Currently when releasing it shows green dot for some reason."

## Root Cause

The issue involved a multi-step rendering sequence:

1. **Release TP** near another TP
2. **Snap positions** together (line ~4586-4591)
3. **Call draw()** for instant feedback (line ~4599)
4. **Problem**: At this point:
   - `this._stretchingNearUL` was still set → showed green "ready to merge" indicator
   - Merge structures (`mergedWith`/`mergedInto`) didn't exist yet → couldn't show purple MP
5. **Merge logic executes** (line ~5070-5089)
6. **No draw() after merge** → purple MP never appeared until next user action

### Visual Sequence (Before Fix)

```
User releases TP
    ↓
Snap to position
    ↓
Draw() called → Shows GREEN DOT (merge indicator still active)
    ↓
Merge structures created → Purple MP data exists
    ↓
(No draw() call) → Purple MP never shows
    ↓
User sees green dot stuck on screen ❌
```

## The Fix

### Two Changes Required

#### 1. Clear Green Indicator (Line ~4593-4595)

```javascript
// CRITICAL: Clear the "near UL" indicator to show purple MP, not green dot
// This ensures the instant draw shows the final MP state, not the "ready to merge" state
this._stretchingNearUL = null;
```

**Effect**: Prevents green "ready to merge" indicator from showing

#### 2. Draw After Merge Completes (Line ~5101-5103)

```javascript
// INSTANT PURPLE MP: Draw immediately after merge to show purple MP, not gray TP
// This completes the visual transition: gray TPs → green indicator → purple MP
this.draw();
```

**Effect**: Updates display to show purple MP as soon as merge structures exist

### Visual Sequence (After Fix)

```
User releases TP
    ↓
Snap to position
    ↓
Clear green indicator ✅
    ↓
Draw() → Shows endpoints at same position (no green ring)
    ↓
Merge structures created ✅
    ↓
Draw() → Shows PURPLE MP ✅
    ↓
User sees purple MP immediately! 🎉
```

## Technical Details

### Green Indicator Code (Line ~13109-13140)

The green "ready to merge" indicator is drawn when:
```javascript
if (isStretching && this._stretchingNearUL) {
    // Draw green ring around target TP
    this.ctx.strokeStyle = '#2ecc71'; // Green - ready to merge
    // ...
}
```

By clearing `this._stretchingNearUL` before the first draw(), this code doesn't execute.

### Purple MP Code (Line ~12975-13033)

The purple MP is drawn when:
```javascript
if (startIsMP && !startAttached && !arrowAtStart) {
    // Draw purple MP
    this.ctx.fillStyle = '#9b59b6'; // Purple
    // ...
}
```

`startIsMP` is only true when the link has `mergedWith` or `mergedInto` structures, which are created during the merge logic. By calling draw() immediately after creating these structures, the purple MP appears.

## Animation Timeline

### Frame 1 (Release + Snap)
- Endpoints snap to same position
- Green indicator cleared
- Draw() shows both endpoints at connection point

### Frame 2 (After Merge)
- Merge structures created (`mergedWith`/`mergedInto`)
- Draw() shows purple MP
- Complete visual transition

**Total time**: < 1ms (feels instant to user)

## Testing

1. Create UL1 and UL2
2. Drag UL1 TP toward UL2 TP
3. **See green ring** appear (indicates merge range)
4. **Release TP**
5. **Observe**: 
   - ✅ Green ring disappears immediately
   - ✅ Purple MP appears immediately
   - ❌ NO green dot stuck on screen

## Benefits

✅ **Clean visual transition** - No green indicator after release
✅ **Instant purple MP** - Shows final state immediately  
✅ **Professional feel** - Smooth, responsive animation
✅ **Matches user expectation** - Purple MP appears when merge completes

## Related Features

- Instant TP merge animation (snap on release)
- BUL connection logic (all TP combinations)
- MP visual feedback and numbering

## Impact

**Very Low Risk**: Added two simple operations:
1. Clear a flag (`this._stretchingNearUL = null`)
2. Add one draw() call after merge

No logic changes, only visual timing improvements.





