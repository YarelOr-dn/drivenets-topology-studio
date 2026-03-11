# Text Rotation Enhancements - December 4, 2025

## Overview

Enhanced text rotation controls with adaptive sizing, arc-based angle meter, and +/- degree format.

## Features Implemented

### 1. Adaptive Resize/Rotate Dots ✅

**Before**: Dots at fixed distance from text (always 5px from bounding box)

**After**: Dots adjust to text size for better UX

**Implementation** (Line ~13453):
```javascript
// Calculate handle distance based on text dimensions
const handleOffset = Math.max(8, Math.min(15, Math.sqrt(w * w + h * h) / 20));

const corners = [
    { x: -w/2 - handleOffset, y: -h/2 - handleOffset, type: 'resize' },
    { x: w/2 + handleOffset, y: -h/2 - handleOffset, type: 'rotation' },
    // ...
];
```

**Result**: 
- Small text → Dots closer (8px min)
- Large text → Dots farther (15px max)
- Proportional to diagonal size

---

### 2. Arc-Based Angle Meter ✅

**Feature**: Visual arc curving around the rotation dot showing current angle

**Implementation** (Lines ~13471-13511):

**Components**:
1. **Background arc** - Full circle (subtle white)
2. **Progress arc** - From 0° to current angle (bright green)
3. **Angle text** - On arc endpoint with +/- format
4. **Outline** - Black stroke for visibility

**Visual Design**:
```
        +45°  ← Text on arc
         /
    (....) ← Green arc showing angle
   /      \
  (   🟢   ) ← Rotation dot
   \      /
    (____) ← Background circle
```

**Code**:
```javascript
// Background arc (full circle)
this.ctx.arc(corner.x, corner.y, arcRadius, 0, Math.PI * 2);
this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';

// Progress arc (0° to current angle)
this.ctx.arc(corner.x, corner.y, arcRadius, 
    -Math.PI / 2,  // Start at top (0°)
    -Math.PI / 2 + (normalizedAngle * Math.PI / 180));  // End at current angle
this.ctx.strokeStyle = '#2ecc71'; // Bright green

// Angle text positioned on arc
const textAngle = -Math.PI / 2 + (normalizedAngle * Math.PI / 180);
const textRadius = arcRadius + 12;
const textX = corner.x + Math.cos(textAngle) * textRadius;
const textY = corner.y + Math.sin(textAngle) * textRadius;
```

**Angle Display**:
- Uses +/- format (e.g., "+45°" or "-90°")
- Positioned on the arc endpoint
- Curves around the rotation dot
- Always readable (horizontal orientation)

---

### 3. +/- Degrees in Text Editor ✅

**Before**: Slider 0-360°

**After**: Number input + slider, both support -180° to +180°

**Implementation**:

**HTML** (`index.html` line ~449):
```html
<div style="display: flex; gap: 8px; align-items: center;">
    <input type="number" id="editor-rotation" 
           min="-180" max="180" value="0" step="1"
           placeholder="+/-">
    <span id="editor-rotation-value">0°</span>
    <input type="range" id="editor-rotation-slider" 
           min="-180" max="180" value="0">
</div>
<div style="font-size: 9px;">
    <span>-180° (CCW)</span>
    <span>0°</span>
    <span>+180° (CW)</span>
</div>
```

**Features**:
- ✅ Number input: Type exact value with +/- sign
- ✅ Slider: Visual control -180 to +180
- ✅ Both sync in real-time
- ✅ Color gradient: Red (negative) → Yellow (0) → Green (positive)
- ✅ Live preview: Updates text immediately

**JavaScript** (Lines ~967-993):
```javascript
// Number input listener
editorRotation.addEventListener('input', (e) => {
    const value = parseInt(e.target.value) || 0;
    const clamped = Math.max(-180, Math.min(180, value));
    // Sync slider and display
    editorRotationSlider.value = clamped;
    editorRotationValue.textContent = `${clamped >= 0 ? '+' : ''}${clamped}°`;
});

// Slider listener (mirrors number input)
editorRotationSlider.addEventListener('input', (e) => {
    const value = parseInt(e.target.value) || 0;
    editorRotation.value = value;
    editorRotationValue.textContent = `${value >= 0 ? '+' : ''}${value}°`;
});
```

**Live Preview** (Lines ~9346-9368):
```javascript
this.livePreviewRotation = (e) => {
    const value = parseInt(e.target.value) || 0;
    // Convert -180 to +180 range to 0-360 for storage
    const normalized = value < 0 ? value + 360 : value;
    this.editingText.rotation = normalized;
    // Sync all controls
    rotationSlider.value = value;
    rotationValue.textContent = `${value >= 0 ? '+' : ''}${value}°`;
    this.draw(); // Live preview!
};
```

---

## Visual Examples

### Arc Meter at Different Angles

**0° (No rotation)**:
```
    ⚪ ← 0° text (subtle arc)
   ( )
  (🟢)
```

**+45° (Clockwise)**:
```
     +45°
      /
   (../
  (🟢 )
```

**-90° (Counter-clockwise)**:
```
  -90°
    |
   (|)
  (🟢)
```

**+180° (Flipped)**:
```
  +180°
     |
   (_)
  (🟢)
```

---

## Usage

### Canvas Interaction
1. Select text
2. **See**: Resize dots at corners, rotation dot (green) at top-right
3. **See**: Arc curving around rotation dot showing current angle
4. **Drag** rotation dot → Arc animates, angle updates in real-time

### Text Editor
1. Double-click text
2. **Type** rotation: -90 (or +45, etc.)
3. **Or use** slider to drag -180 to +180
4. **See**: Live preview updates, arc meter animates
5. **Observe**: +/- format everywhere

---

## Technical Details

### Angle Conversion

**Internal Storage**: 0-360° (standard format)
**User Display**: -180° to +180° (intuitive format)

**Conversion**:
```javascript
// Display to storage
display = -90
storage = -90 + 360 = 270

// Storage to display
storage = 270
display = 270 > 180 ? 270 - 360 : 270 = -90
```

### Arc Positioning

- **Arc radius**: dot radius + 8px (curves around outside)
- **Start angle**: -π/2 (top, 0°)
- **End angle**: -π/2 + (current angle in radians)
- **Text position**: On arc endpoint, offset +12px

### Adaptive Sizing Formula

```javascript
handleOffset = max(8, min(15, sqrt(width² + height²) / 20))
```

This creates smooth scaling:
- Diagonal 100px → offset 8px (minimum)
- Diagonal 200px → offset 10px
- Diagonal 300px → offset 15px (maximum)

---

## Benefits

✅ **Better UX**: Dots adapt to text size
✅ **Visual Feedback**: Arc shows rotation clearly
✅ **Intuitive Input**: +/- degrees match common usage
✅ **Real-time Preview**: All controls sync instantly
✅ **Professional Look**: Curved arc meter is polished

---

## Testing

1. Create text
2. Select it
3. Observe:
   - ✅ 4 corner dots (3 blue resize, 1 green rotate)
   - ✅ Arc curving around rotation dot
   - ✅ Angle displayed on arc (e.g., "+0°")
4. Drag rotation dot
5. Observe:
   - ✅ Arc animates smoothly
   - ✅ Angle updates in real-time
   - ✅ Shows +/- format
6. Double-click to edit
7. Enter rotation: -90
8. Observe:
   - ✅ Text rotates counter-clockwise
   - ✅ Arc shows -90°
   - ✅ Slider syncs
9. Use slider to adjust
10. Observe: All controls stay synchronized

---

## Related Features

- Text placement (continuous mode)
- Text dragging (smooth, no disappearing)
- Text editor (live preview)
- Rotation by dragging dot
- Resize by dragging corners

---

## Date

December 4, 2025





