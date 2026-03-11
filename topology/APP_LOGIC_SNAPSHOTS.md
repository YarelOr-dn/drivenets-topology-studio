# Network Topology Creator - Logic Snapshots
## Created: Dec 5, 2025

This document contains snapshots of all major logic sections in the application.

---

## SNAPSHOT 1: Core Application Initialization
**File:** `topology.js` (Lines 3-100)
**Description:** TopologyEditor class constructor and core state management

### Key Components:
- **Canvas & Context Setup**: Initializes 2D canvas context for rendering
- **Object Management**: Arrays for objects, selected objects, multi-select support
- **Tool System**: Current tool tracking (select, link, device, text)
- **Drag & Drop**: Dragging, panning, and object movement state
- **Zoom & Pan**: Persistent zoom level (0.25-3x) and pan offset saved to localStorage
- **Device Counters**: Auto-incrementing IDs for devices, links, text (deviceIdCounter, linkIdCounter, textIdCounter)
- **Multi-Select Mode**: Support for selecting and moving multiple objects
- **Link Modes**:
  - `linkCurveMode`: Curved links with magnetic repulsion
  - `linkContinuousMode`: Chain links together continuously
  - `linkStickyMode`: Links snap to devices automatically
  - `linkULEnabled`: Unbound Links feature toggle
- **Touch/Trackpad Support**: Long-press detection, pinch zoom, two-finger gestures
- **Visual Settings**: Dark mode, grid zoom, link style (solid/dashed/arrow)
- **Collision Detection**: Device collision and magnetic field strength

### State Variables (Critical):
```javascript
this.objects = [];                    // All topology objects
this.selectedObject = null;           // Current selection
this.currentTool = 'select';          // Active tool
this.zoom = 1;                        // Zoom level (saved to localStorage)
this.panOffset = { x: 0, y: 0 };     // Pan position (saved to localStorage)
this.linking = false;                 // Link creation in progress
this.linkStart = null;                // Link starting point
this.multiSelectMode = false;         // Multi-select active
this.darkMode = false;                // UI theme
```

---

## SNAPSHOT 2: Device Management System
**File:** `topology.js` (Lines 300-500 approx)
**Description:** Device creation, placement, and interaction logic

### Key Features:
- **Device Types**: Router, Switch (with visual icons)
- **Auto-Numbering**: Devices numbered per type (NCP, NCP-2, etc.)
- **Placement**: Click to place or drag-and-drop
- **Device Properties**:
  - Position (x, y)
  - Radius (default 30px)
  - Color (customizable)
  - Rotation angle
  - Label text
- **Device Collision**: Optional collision detection and magnetic repulsion
- **Movable Devices**: Chain reaction movement when devices collide

### Device Object Structure:
```javascript
{
  id: 'device_0',
  type: 'device',
  deviceType: 'router',      // or 'switch'
  x: 100,
  y: 100,
  radius: 30,
  color: '#4CAF50',
  rotation: 0,
  label: 'NCP'
}
```

---

## SNAPSHOT 3: Link Creation & Management
**File:** `topology.js` (Lines 800-1500 approx)
**Description:** Link types, connection logic, and visual rendering

### Link Types:
1. **QL (Quick Link)**: Direct device-to-device connection
2. **UL (Unbound Link)**: Free-floating link endpoints (not attached to devices)
3. **BUL (Bound-Unbound Link)**: One end attached to device, one end free
4. **Merged Links**: Multiple links sharing connection points (TP/MP system)

### Link Features:
- **Connection Points**: 
  - TP (Tap Point): Point where link touches device
  - MP (Moving Point): Intermediate waypoint on link path
- **Auto-Stick**: Links automatically snap to nearby devices
- **Continuous Mode**: Chain multiple links together
- **Link Styles**: Solid, dashed, or arrow variants
- **Per-Link Customization**: Individual color, style, and arrow settings
- **Curve Mode**: Magnetic repulsion between parallel links
- **Snap Distance**: UL endpoints snap together within 15px

### Link Object Structure:
```javascript
{
  id: 'link_0',
  type: 'link',
  linkType: 'QL',           // 'QL', 'UL', 'BUL'
  device1: 'device_0',      // First device ID (or null for UL)
  device2: 'device_1',      // Second device ID (or null for UL)
  tp1: { x: 100, y: 100 },  // Tap point 1
  tp2: { x: 200, y: 200 },  // Tap point 2
  color: '#666',
  style: 'solid',           // 'solid', 'dashed', 'arrow'
  showArrows: true
}
```

---

## SNAPSHOT 4: TP/MP Numbering System
**File:** `topology.js` (BUL-related sections)
**Description:** Connection point numbering and management

### Numbering Rules:
- **TP (Tap Point)**: Numbered 1 or 2 based on device ID (lower ID gets TP1)
- **MP (Moving Point)**: Numbered per-BUL, not globally
- **Per-BUL MPs**: Each BUL has its own MP sequence (MP1, MP2, MP3...)
- **Symmetric Handling**: Head and tail of multi-link chains treated equally

### Key Logic:
```javascript
// Lower device ID always gets TP1
if (deviceId1 < deviceId2) {
  link.tp1 = pointOnDevice1;
  link.tp2 = pointOnDevice2;
} else {
  link.tp1 = pointOnDevice2;
  link.tp2 = pointOnDevice1;
}

// MPs numbered per-BUL
link.mps = [
  { id: 'mp_1', x: 150, y: 150 },
  { id: 'mp_2', x: 175, y: 175 }
];
```

---

## SNAPSHOT 5: Multi-Select & Marquee Selection
**File:** `topology.js` (Lines 2000-2500 approx)
**Description:** Multiple object selection and group operations

### Features:
- **Marquee Selection**: Drag to select multiple objects in rectangle
- **Multi-Select Mode**: Hold Ctrl/Cmd to add to selection
- **Group Movement**: Move all selected objects together
- **Selection Persistence**: Selected objects remain highlighted
- **Deselection**: Click background to clear selection

### Marquee Logic:
```javascript
// Start marquee on mouse down
this.selectionRectStart = { x: mouseX, y: mouseY };
this.marqueeActive = true;

// Update selection rectangle on drag
this.selectionRectangle = {
  x: Math.min(start.x, current.x),
  y: Math.min(start.y, current.y),
  width: Math.abs(current.x - start.x),
  height: Math.abs(current.y - start.y)
};

// Select all objects within rectangle
this.selectedObjects = this.objects.filter(obj => 
  isInsideRectangle(obj, this.selectionRectangle)
);
```

---

## SNAPSHOT 6: Text Label System
**File:** `topology.js` (Text-related sections)
**Description:** Text placement, editing, and formatting

### Text Features:
- **Placement Modes**: 
  - Single click: Place one text
  - Continuous mode: Place multiple texts
- **Text Properties**:
  - Font size: 8-72px (adjustable)
  - Rotation: 360° rotation capability
  - Color: Customizable
  - Content: Editable via double-click
- **Text Manipulation**:
  - Drag to move
  - Rotation handle for spinning
  - Resize handle for font size
- **Advanced Editor**: Rich text editing panel

### Text Object Structure:
```javascript
{
  id: 'text_0',
  type: 'text',
  x: 200,
  y: 200,
  text: 'Network A',
  fontSize: '14',
  color: '#000000',
  rotation: 0,
  width: 100,    // Calculated from text content
  height: 20     // Calculated from font size
}
```

---

## SNAPSHOT 7: Canvas Rendering Engine
**File:** `topology.js` (render() and draw methods)
**Description:** Visual rendering and animation system

### Rendering Pipeline:
1. **Clear Canvas**: Clear previous frame
2. **Apply Transformations**: Pan offset and zoom
3. **Draw Grid**: Background grid with zoom-aware scaling
4. **Draw Links**: Render all link types with curves/arrows
5. **Draw Devices**: Render device icons and labels
6. **Draw Text**: Render text labels with rotation
7. **Draw Selection**: Highlight selected objects
8. **Draw Tools**: Show active tool indicators (connection points, handles)

### Rendering Features:
- **Grid System**: Adjustable grid with zoom scaling
- **Layer Management**: Links drawn before devices (proper z-index)
- **Selection Highlighting**: Blue outline for selected objects
- **Connection Point Visualization**: TPs and MPs shown as colored circles
- **Link Curves**: Bézier curves for curved links
- **Anti-Aliasing**: Smooth rendering of all shapes
- **Dark Mode**: Alternative color scheme

---

## SNAPSHOT 8: Event Handling System
**File:** `topology.js` (Event listeners)
**Description:** Mouse, keyboard, and touch event processing

### Event Types:
1. **Mouse Events**:
   - `mousedown`: Start drag, link, or selection
   - `mousemove`: Update drag, pan, or link preview
   - `mouseup`: Complete action
   - `wheel`: Zoom or horizontal pan (with Shift)
   - `dblclick`: Edit text or create UL

2. **Keyboard Events**:
   - `Space`: Enable pan mode
   - `Delete/Backspace`: Delete selected objects
   - `Ctrl/Cmd`: Multi-select mode
   - `Alt/Option`: Quick link start
   - `Esc`: Cancel current action

3. **Touch Events**:
   - `touchstart`: Detect taps, long-press
   - `touchmove`: Drag, pan, pinch zoom
   - `touchend`: Complete gesture
   - Two-finger gestures: Pan and pinch zoom

### Event Coordination:
```javascript
// Prevent conflicts between events
if (this.panning) return;           // Don't interact while panning
if (this.dragging) return;          // Don't pan while dragging
if (this.linking) return;           // Don't select while linking
if (this.multiSelectMode) return;   // Different behavior in multi-select
```

---

## SNAPSHOT 9: Save/Load System
**File:** `topology.js` (saveTopology, loadTopology methods)
**Description:** Topology persistence and file format

### Save Format (JSON):
```json
{
  "version": "1.0",
  "objects": [
    { /* device object */ },
    { /* link object */ },
    { /* text object */ }
  ],
  "metadata": {
    "deviceIdCounter": 2,
    "linkIdCounter": 1,
    "textIdCounter": 1,
    "deviceCounters": {
      "router": 1,
      "switch": 0
    }
  }
}
```

### Features:
- **Auto-Save**: Saves to localStorage on every change
- **Export**: Download as timestamped JSON file
- **Import**: Load from JSON file
- **Version Control**: File format versioning
- **Metadata Preservation**: Counters and settings saved
- **Error Handling**: Validation and graceful failure

---

## SNAPSHOT 10: Link Table & Properties Panel
**File:** `index.html` (UI sections)
**Description:** Link management interface and object properties

### Link Table Features:
- **Link List**: Shows all links in topology
- **Link Details**: Device endpoints, type, style
- **Quick Actions**:
  - Delete link
  - Change color
  - Toggle arrows
  - Modify style
- **Platform Support**: VLAN stack and platform type fields
- **Sorting**: Sort by ID, type, or endpoint

### Properties Panel:
- **Device Properties**:
  - Label text
  - Color picker
  - Rotation angle
  - Position (x, y)
- **Link Properties**:
  - Color
  - Style (solid/dashed/arrow)
  - Arrow toggle
  - Endpoints
- **Text Properties**:
  - Content
  - Font size
  - Rotation
  - Color

---

## SNAPSHOT 11: Debugger System
**File:** `debugger.js`
**Description:** Built-in debugging and analysis tools

### Debugger Features:
- **Bug Detection**: Automatic issue detection
- **Severity Levels**: Critical, warning, info
- **Bug Categories**: Race conditions, UI issues, logic errors
- **Bug Alerts**: Bottom-bar notifications
- **Copy Report**: Copy comprehensive bug details
- **Code Conflict Detection**: Identifies conflicting code sections
- **Performance Monitoring**: Track rendering performance
- **State Inspector**: View internal application state

### Bug Alert System:
```javascript
{
  severity: 'CRITICAL',          // or 'WARNING', 'INFO'
  category: 'RACE_CONDITION',    // Bug type
  description: 'Bug details...',
  conflicts: 3,                  // Number of code conflicts
  timestamp: Date.now()
}
```

---

## SNAPSHOT 12: UI Controls & Toolbar
**File:** `index.html` (Toolbar section)
**Description:** User interface and tool controls

### Toolbar Tools:
1. **Select Tool**: Default selection mode
2. **Router/Switch**: Device placement tools
3. **Link Tool**: Create connections
4. **Text Tool**: Add labels
5. **Delete Tool**: Remove objects
6. **Pan Tool**: Canvas navigation

### Utility Buttons:
- **File Menu**: Save, load, export
- **Undo/Redo**: Action history
- **Zoom Controls**: Zoom in/out, reset
- **Grid Toggle**: Show/hide grid
- **Dark Mode**: Theme switcher
- **Settings**: Link modes, collision, numbering

### Mode Toggles:
```javascript
// Link Mode Settings
- Curve Mode: ON/OFF
- Continuous Mode: ON/OFF
- Sticky Mode: ON/OFF
- UL Enabled: ON/OFF

// Device Settings
- Auto-Numbering: ON/OFF
- Collision Detection: ON/OFF
- Movable Devices: ON/OFF

// Visual Settings
- Grid Zoom: ON/OFF
- Link Type Labels: ON/OFF
- Dark Mode: ON/OFF
```

---

## SNAPSHOT 13: Magnetic Repulsion System
**File:** `topology.js` (Magnetic field calculations)
**Description:** Link curve and collision avoidance

### Magnetic Field Logic:
- **Link Repulsion**: Parallel links push away from each other
- **Adjustable Strength**: 1-80 field strength setting
- **Distance-Based**: Repulsion decreases with distance
- **Performance Optimized**: Throttled updates to prevent lag
- **Visual Feedback**: Curved links show repulsion effect

### Calculation:
```javascript
// Calculate magnetic repulsion between two links
function calculateMagneticForce(link1, link2, strength) {
  const distance = distanceBetweenLinks(link1, link2);
  const force = strength / (distance * distance);
  return Math.min(force, MAX_FORCE);
}

// Apply to link curve
link.curveOffset = magneticForce * perpendicular_direction;
```

---

## SNAPSHOT 14: Double-Tap & Gesture Detection
**File:** `topology.js` (Touch event handlers)
**Description:** Touch gesture recognition system

### Gesture Types:
1. **Single Tap**: Select object
2. **Double Tap**: 
   - On device: Start link
   - On background: Place UL (if fast enough)
   - On text: Edit text
3. **Long Press**: Enable movement/selection
4. **Pinch Zoom**: Two-finger zoom
5. **Two-Finger Pan**: Two-finger scroll

### Detection Logic:
```javascript
// Double-tap detection
const timeSinceLastTap = now - this.lastTapTime;
const distanceFromLastTap = distance(pos, this._lastTapPos);

if (timeSinceLastTap < this.doubleTapDelay && 
    distanceFromLastTap < this.doubleTapTolerance) {
  // Double tap detected
  handleDoubleTap();
}

// Long press detection
this.longPressTimer = setTimeout(() => {
  handleLongPress();
}, this.longPressDelay);
```

---

## SNAPSHOT 15: UL Snap & Merge System
**File:** `topology.js` (UL endpoint handling)
**Description:** Unbound link snapping and merging logic

### UL Features:
- **Free Endpoints**: Links not attached to devices
- **Snap Distance**: 15px threshold for automatic snapping
- **Endpoint Merging**: Multiple ULs can share endpoints
- **Connection Points**: Merged endpoints shown as circles
- **Visual Feedback**: Highlight when within snap range
- **Auto-Convert**: UL → BUL when one end attaches to device
- **Auto-Convert**: BUL → QL when both ends attach to devices

### Snap Logic:
```javascript
// Check if UL endpoint is near another endpoint
function checkULSnap(endpoint, allEndpoints, snapDistance = 15) {
  for (const other of allEndpoints) {
    const dist = distance(endpoint, other);
    if (dist < snapDistance) {
      return other; // Snap to this endpoint
    }
  }
  return null;
}

// Merge UL endpoints
if (nearbyEndpoint) {
  endpoint.x = nearbyEndpoint.x;
  endpoint.y = nearbyEndpoint.y;
  endpoint.merged = true;
}
```

---

## Summary of Major Logic Sections

### Core Systems:
1. ✅ Application Initialization & State Management
2. ✅ Device Management (Creation, Placement, Collision)
3. ✅ Link Creation (QL, UL, BUL types)
4. ✅ TP/MP Numbering System
5. ✅ Multi-Select & Marquee Selection
6. ✅ Text Label System
7. ✅ Canvas Rendering Engine
8. ✅ Event Handling (Mouse, Keyboard, Touch)
9. ✅ Save/Load System
10. ✅ Link Table & Properties Panel
11. ✅ Debugger System
12. ✅ UI Controls & Toolbar
13. ✅ Magnetic Repulsion System
14. ✅ Double-Tap & Gesture Detection
15. ✅ UL Snap & Merge System

### File Structure:
- **index.html**: Main HTML structure, UI elements, toolbars
- **topology.js**: Core application logic (14,000+ lines)
- **styles.css**: Visual styling and themes
- **debugger.js**: Debugging and analysis tools
- **topology-momentum.js**: Physics simulation (optional)
- **topology-history.js**: Undo/redo system

### Key Technologies:
- HTML5 Canvas API
- JavaScript ES6+ Classes
- LocalStorage for persistence
- Touch/Pointer Events API
- JSON file format
- CSS Grid/Flexbox for UI

---

## Next Steps for Development

### Recommended Enhancements:
1. **Export to Image**: PNG/SVG export functionality
2. **Keyboard Shortcuts Panel**: Help overlay showing all shortcuts
3. **Snap to Grid**: Option to snap devices to grid points
4. **Link Labels**: Add text labels directly on links
5. **Group/Ungroup**: Group multiple objects together
6. **Layers**: Organize objects into layers
7. **Templates**: Save and load device/topology templates
8. **Collaboration**: Real-time multi-user editing
9. **Version History**: Track changes over time
10. **Import/Export**: Support for other formats (GNS3, Draw.io)

---

*End of Logic Snapshots*
*Generated: December 5, 2025*




