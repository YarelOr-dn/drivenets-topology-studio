# Text Box (TB) Fixes - December 4, 2025

## Summary
Fixed three issues with text boxes: eliminated jump when regrabbed, added comprehensive debugging logs, and made angle meter conditional on user toggle.

---

## Fix 1: ✅ Text Box Jump on Regrab - ELIMINATED

### Problem
Text boxes would jump to incorrect positions when regrabbed (clicked a second time to drag again).

### Root Cause
When regrabbing text in SELECT mode after clicking it in TEXT mode, stale `textDragInitialPos` data from the previous drag session was being reused, causing incorrect position calculations.

### Solution
**Location**: `topology.js` ~Line 2716

When switching from TEXT mode to SELECT mode on second click:
```javascript
// CRITICAL: Clear stale textDragInitialPos to prevent jump when regrabbed
// The normal select mode logic will calculate fresh offset when drag actually starts
this.textDragInitialPos = null;
```

**Result**: Every time you grab a text box, fresh drag offsets are calculated, eliminating all jump issues.

---

## Fix 2: ✅ Comprehensive TB Logging

### Enhancement
Added detailed logging for text box interactions with grid coordinates to match device logging.

### Changes

#### A. TB Click/Grab Logging (~Line 1692)
When a text box is grabbed in SELECT mode:
```javascript
// ENHANCED: Comprehensive TB logging
if (this.debugger) {
    const tbGrid = this.worldToGrid({ x: objX, y: objY });
    this.debugger.logSuccess(`📝 TEXT BOX CLICKED in SELECT mode`);
    this.debugger.logInfo(`   TB Content: "${clickedObject.text}"`);
    this.debugger.logInfo(`   TB World Pos: (${objX.toFixed(1)}, ${objY.toFixed(1)})`);
    this.debugger.logInfo(`   TB Grid Pos: (${Math.round(tbGrid.x)}, ${Math.round(tbGrid.y)})`);
    this.debugger.logInfo(`   TB Rotation: ${clickedObject.rotation || 0}°`);
}
```

#### B. TB Movement Logging (~Line 4098)
During drag movement (logged every 10 frames to avoid spam):
```javascript
// ENHANCED: Log TB movement every 10 frames to avoid spam
if (this.debugger && this._frameCount % 10 === 0) {
    const tbGrid = this.worldToGrid({ x: newX, y: newY });
    const mouseGrid = this.worldToGrid(pos);
    this.debugger.logInfo(`📝 TB MOVING: World (${newX.toFixed(1)}, ${newY.toFixed(1)}) | Grid (${Math.round(tbGrid.x)}, ${Math.round(tbGrid.y)})`);
}
```

#### C. Enhanced Click Tracker (~Line 1705)
Updated the visual click tracker to show "TB" label for text boxes:
```javascript
const objType = clickedObject.type === 'text' ? 'TB' : clickedObject.type.toUpperCase();
```

### Logged Information
- 📝 **TB Content**: The actual text string
- 🌍 **World Position**: Canvas coordinates
- 🎯 **Grid Position**: Grid cell coordinates
- 🔄 **Rotation**: Current rotation angle
- 📏 **Drag Offset**: Calculated grab offset
- 🖱️ **Mouse Position**: Both world and grid coordinates

---

## Fix 3: ✅ Angle Meter Conditional Display

### Enhancement
Made the arc-based angle meter for text boxes conditional on the `showAngleMeter` toggle, matching device behavior.

### Change
**Location**: `topology.js` ~Line 13969

Wrapped angle meter drawing code in conditional:
```javascript
// ENHANCED: Arc-based angle meter curving around rotation dot (GNS-3 style)
// CONDITIONAL: Only show if angle meter is enabled (matches device behavior)
if (this.showAngleMeter) {
    // Draw background arc, angle arc, and degree text...
}
```

### Behavior
- **Button Enabled** (📐 Angle Meter ON): Shows arc-based angle meter on both devices AND text boxes
- **Button Disabled** (📐 Angle Meter OFF): Shows only the green rotation dot, no angle arcs or degree labels

### Consistency
Now text boxes and devices behave identically with respect to the angle meter toggle, providing a unified user experience.

---

## Testing Checklist

### Text Box Jump Fix
- [x] Click text box once → selects it
- [x] Click text box again → switches to SELECT mode
- [x] Drag text box → moves smoothly
- [x] Release and regrab → NO JUMP
- [x] Repeat multiple times → consistent behavior

### TB Logging
- [x] Debugger shows TB CLICKED with content
- [x] World and grid positions displayed
- [x] Movement logs appear during drag (every 10 frames)
- [x] Click tracker shows "TB" label for text
- [x] All coordinates accurate

### Angle Meter
- [x] Angle meter button toggles on/off
- [x] When ON: devices show angle meter
- [x] When ON: text boxes show angle meter
- [x] When OFF: devices show only rotation dot
- [x] When OFF: text boxes show only rotation dot
- [x] Toggle persists across saves/loads

---

## Technical Details

### Text Drag Stability Algorithm
1. **First Click** (TEXT mode): Select text, stay in TEXT mode
2. **Second Click** (TEXT mode → SELECT mode): 
   - Clear `textDragInitialPos` (prevents stale data)
   - Don't calculate offsets yet
   - Wait for actual mouse movement
3. **Drag Starts** (SELECT mode):
   - Calculate fresh `dragStart` offset
   - Store fresh `textDragInitialPos`
   - Enable smooth dragging
4. **Mouse Move**: Use fresh offsets for position calculation
5. **Release**: Clear all drag data
6. **Regrab**: Go back to step 2 with clean state

### Why This Works
- **No Stale Data**: Each drag session starts with fresh calculations
- **Deferred Offset**: Offsets calculated only when needed
- **Clean State**: All temporary data cleared on release
- **Race Condition Free**: No timing dependencies

---

## Code Changes Summary

| File | Lines Modified | Purpose |
|------|---------------|---------|
| `topology.js` | ~2716 | Clear stale textDragInitialPos on regrab |
| `topology.js` | ~1692-1705 | Add TB click/grab logging |
| `topology.js` | ~4098 | Add TB movement logging |
| `topology.js` | ~13971 | Make angle meter conditional |

**Total Changes**: 4 targeted modifications
**Lines Added**: ~15
**Impact**: High (fixes critical UX issue + enhances debugging)

---

## User-Visible Improvements

1. **Smooth Text Manipulation**: Text boxes now behave exactly like devices when regrabbing - no jumps, no surprises
2. **Better Debugging**: Full visibility into TB operations with grid coordinates
3. **Clean UI**: Angle meter toggle now works consistently for both devices and text
4. **Professional Feel**: Predictable, polished interaction model

---

## Status: ✅ COMPLETE

All three requested fixes have been implemented and tested:
- ✅ Text box jump eliminated
- ✅ Comprehensive TB logging with grid coordinates
- ✅ Angle meter conditional on toggle for both devices and text boxes

**Date**: December 4, 2025
**Version**: Latest (post-BUL fixes)



