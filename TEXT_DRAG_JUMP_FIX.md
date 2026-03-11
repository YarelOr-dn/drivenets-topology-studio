# Fix: Text Drag Jump After Selection

## Problem

Text boxes were jumping massively when dragged:
- Grab at (2534, 718)
- Jump to (24, -82)
- Distance: 2634px! ❌

## Root Cause

When clicking a selected text box the second time (to enter select mode), the code was:
1. Setting `textDragInitialPos` with current mouse position
2. Switching to select mode
3. But mouse hasn't actually moved yet!
4. When user then drags, calculation uses wrong initial position
5. Massive jump occurs

### The Bug (Lines 2720-2728)

```javascript
// Second click to enter select mode
this.dragStart = { x: pos.x - objX, y: pos.y - objY };
this.dragStartPos = { x: objX, y: objY };
this.textDragInitialPos = {
    textX: objX,
    textY: objY,
    mouseX: pos.x,    // ← Set on click!
    mouseY: pos.y,    // ← Set on click!
    // ...
};
```

Then when dragging:
```javascript
if (this.selectedObject.type === 'text' && this.textDragInitialPos) {
    const mouseDx = pos.x - this.textDragInitialPos.mouseX;  // ← Uses click position!
    const mouseDy = pos.y - this.textDragInitialPos.mouseY;
    
    newX = this.textDragInitialPos.textX + mouseDx;  // ← Huge delta!
    newY = this.textDragInitialPos.textY + mouseDy;
}
```

## The Fix

**Removed** the drag offset setup from the second click:

```javascript
if (isAlreadySelected) {
    // Second click → Switch to SELECT mode
    this.setMode('select');
    
    // DON'T set drag offsets here!
    // Let normal select mode handle it when drag actually starts
}
```

Now `textDragInitialPos` is only set when:
1. Actually starting a drag in select mode (normal path)
2. Not on a premature second click

## Result

✅ No more massive jumps
✅ Text drags smoothly
✅ Offset calculated correctly when drag actually starts
✅ Click to select, then drag = smooth

## Date

December 4, 2025



