# UI & Visual Layer - Snapshots
## Network Topology Creator - Interface Documentation
## Created: Dec 5, 2025

This document contains snapshots of all major UI components and visual design elements.

---

## UI SNAPSHOT 1: Top Bar Navigation
**File:** `index.html` (Lines 46-50) + `styles.css` (Lines 30-60)
**Description:** Main navigation bar with file operations and utilities

### Visual Design:
```css
.top-bar {
    position: fixed;
    top: 0;
    height: 50px;
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    z-index: 1001;
}
```

### Components:
- **File Menu Button**: SVG icon, opens dropdown for save/load
- **Utility Buttons**: Quick access to common operations
- **Collapse Toggle**: Arrow button to hide/show top bar
- **Dark Mode Toggle**: Theme switcher

### Features:
- Gradient background (dark blue-gray)
- Smooth collapse animation (translateY)
- Shadow for depth perception
- Gap-spaced button layout
- Hover effects on all buttons

### Behavior:
- Collapsed state: slides up 50px
- Canvas expands to full height when collapsed
- Toggle button remains visible (attached to bar bottom)
- Smooth 0.3s ease transitions

---

## UI SNAPSHOT 2: Left Toolbar (Tool Palette)
**File:** `index.html` (Toolbar section) + `styles.css` (Lines 200-400)
**Description:** Vertical tool palette for device/link/text creation

### Visual Structure:
```
┌─────────────┐
│   SELECT    │ ← Currently active (blue highlight)
├─────────────┤
│   ROUTER    │
├─────────────┤
│   SWITCH    │
├─────────────┤
│    LINK     │
├─────────────┤
│    TEXT     │
├─────────────┤
│   DELETE    │
└─────────────┘
```

### Styling:
```css
.toolbar {
    position: fixed;
    left: 0;
    top: 50px;
    width: 70px;
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
}

.tool-btn {
    width: 60px;
    height: 60px;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: all 0.3s ease;
}

.tool-btn.active {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
}

.tool-btn:hover {
    background: rgba(52, 152, 219, 0.1);
    transform: scale(1.05);
}
```

### Features:
- SVG icons for each tool
- Active tool highlighted in blue gradient
- Hover scale effect (1.05x)
- Tooltips on hover
- Smooth color transitions
- Collapse toggle (arrow button)

---

## UI SNAPSHOT 3: Right Panel (Properties & Link Table)
**File:** `index.html` (Right panel sections) + `styles.css` (Lines 500-800)
**Description:** Object properties editor and link management table

### Panel Structure:
```
┌─────────────────────────────────┐
│  PROPERTIES                  [-]│
├─────────────────────────────────┤
│  Selected: device_0              │
│  ┌─────────────────────────┐   │
│  │ Label: [NCP          ] │   │
│  │ Color: [🎨          ] │   │
│  │ X: [100]  Y: [100]     │   │
│  │ Rotation: [0°]         │   │
│  └─────────────────────────┘   │
├─────────────────────────────────┤
│  LINK TABLE                  [-]│
├─────────────────────────────────┤
│ ┌───┬─────┬──────┬──────┬───┐ │
│ │ ID│Type │Start │End   │Del│ │
│ ├───┼─────┼──────┼──────┼───┤ │
│ │ 0 │ QL  │NCP   │NCP-2 │ X │ │
│ │ 1 │ BUL │NCP-2 │(free)│ X │ │
│ │ 2 │ UL  │(free)│(free)│ X │ │
│ └───┴─────┴──────┴──────┴───┘ │
└─────────────────────────────────┘
```

### Properties Panel Sections:

#### Device Properties:
- Label input field
- Color picker
- Position (X, Y) number inputs
- Rotation slider (0-360°)
- Delete button

#### Link Properties:
- Link style dropdown (solid/dashed/arrow)
- Color picker
- Show/hide arrows toggle
- Start/end device labels
- Delete button

#### Text Properties:
- Text content textarea
- Font size slider (8-72px)
- Rotation slider (0-360°)
- Color picker
- Delete button

### Link Table Features:
- Sortable columns
- Row hover highlight
- Delete button per row
- Color indicator dots
- Link type badges (QL/UL/BUL)
- Platform/VLAN fields
- Scroll for many links

### Styling:
```css
.properties-panel {
    position: fixed;
    right: 0;
    top: 50px;
    width: 300px;
    background: white;
    border-left: 1px solid #ddd;
    overflow-y: auto;
    max-height: calc(100vh - 50px);
}

.property-group {
    padding: 15px;
    border-bottom: 1px solid #eee;
}

.property-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
    font-weight: 600;
}

.property-input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.link-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
}

.link-table th {
    background: #f5f5f5;
    padding: 8px 4px;
    text-align: left;
    font-weight: 600;
    color: #555;
}

.link-table td {
    padding: 6px 4px;
    border-bottom: 1px solid #eee;
}

.link-table tr:hover {
    background: rgba(52, 152, 219, 0.05);
}
```

---

## UI SNAPSHOT 4: Canvas & Grid System
**File:** `index.html` (Canvas element) + `topology.js` (render methods)
**Description:** Main drawing area with grid background

### Canvas Configuration:
```javascript
// Canvas setup
canvas.width = window.innerWidth - 370; // Minus toolbars
canvas.height = window.innerHeight - 50; // Minus top bar
canvas.style.background = '#ffffff'; // Light mode
// OR
canvas.style.background = '#1a1a1a'; // Dark mode
```

### Grid Rendering:
```javascript
// Draw grid background
function drawGrid() {
    const gridSize = 20 * this.zoom; // Zoom-aware grid
    const offsetX = this.panOffset.x % gridSize;
    const offsetY = this.panOffset.y % gridSize;
    
    this.ctx.strokeStyle = this.darkMode ? 
        'rgba(255, 255, 255, 0.05)' :  // Dark mode: light lines
        'rgba(0, 0, 0, 0.08)';         // Light mode: dark lines
    this.ctx.lineWidth = 1;
    
    // Vertical lines
    for (let x = offsetX; x < this.canvas.width; x += gridSize) {
        this.ctx.beginPath();
        this.ctx.moveTo(x, 0);
        this.ctx.lineTo(x, this.canvas.height);
        this.ctx.stroke();
    }
    
    // Horizontal lines
    for (let y = offsetY; y < this.canvas.height; y += gridSize) {
        this.ctx.beginPath();
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(this.canvas.width, y);
        this.ctx.stroke();
    }
}
```

### Features:
- 20px base grid size
- Scales with zoom level
- Offset follows pan position
- Different colors for light/dark mode
- Semi-transparent for subtlety
- Toggle on/off via settings

---

## UI SNAPSHOT 5: Device Rendering
**File:** `topology.js` (drawDevice method)
**Description:** Visual representation of network devices

### Router Icon:
```javascript
function drawRouter(x, y, radius, color, selected) {
    // Outer circle
    this.ctx.beginPath();
    this.ctx.arc(x, y, radius, 0, Math.PI * 2);
    this.ctx.fillStyle = color || '#4CAF50';
    this.ctx.fill();
    
    // Selection highlight
    if (selected) {
        this.ctx.strokeStyle = '#2196F3';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
    }
    
    // Border
    this.ctx.strokeStyle = '#333';
    this.ctx.lineWidth = 2;
    this.ctx.stroke();
    
    // Router symbol (four arrows pointing outward)
    this.ctx.strokeStyle = 'white';
    this.ctx.lineWidth = 2;
    
    // Draw 4 arrows at 0°, 90°, 180°, 270°
    for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 2) {
        const startX = x + Math.cos(angle) * (radius * 0.3);
        const startY = y + Math.sin(angle) * (radius * 0.3);
        const endX = x + Math.cos(angle) * (radius * 0.7);
        const endY = y + Math.sin(angle) * (radius * 0.7);
        
        // Arrow shaft
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endX, endY);
        this.ctx.stroke();
        
        // Arrowhead
        const arrowSize = 4;
        const arrowAngle = Math.PI / 6;
        this.ctx.beginPath();
        this.ctx.moveTo(endX, endY);
        this.ctx.lineTo(
            endX - arrowSize * Math.cos(angle - arrowAngle),
            endY - arrowSize * Math.sin(angle - arrowAngle)
        );
        this.ctx.moveTo(endX, endY);
        this.ctx.lineTo(
            endX - arrowSize * Math.cos(angle + arrowAngle),
            endY - arrowSize * Math.sin(angle + arrowAngle)
        );
        this.ctx.stroke();
    }
    
    // Label below device
    this.ctx.fillStyle = this.darkMode ? '#fff' : '#000';
    this.ctx.font = '12px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(device.label, x, y + radius + 15);
}
```

### Switch Icon:
```javascript
function drawSwitch(x, y, radius, color, selected) {
    // Similar to router but with different symbol
    // Outer circle (same as router)
    // ...
    
    // Switch symbol (grid of dots representing ports)
    this.ctx.fillStyle = 'white';
    const dotRadius = 2;
    const spacing = 8;
    
    // 3x3 grid of dots
    for (let row = -1; row <= 1; row++) {
        for (let col = -1; col <= 1; col++) {
            const dotX = x + col * spacing;
            const dotY = y + row * spacing;
            this.ctx.beginPath();
            this.ctx.arc(dotX, dotY, dotRadius, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
}
```

### Visual Properties:
- Default radius: 30px
- Customizable color
- Blue highlight when selected (3px stroke)
- Label text below icon
- Rotation support (entire device rotates)
- Shadow effects (optional)

---

## UI SNAPSHOT 6: Link Rendering
**File:** `topology.js` (drawLink method)
**Description:** Visual representation of connections

### Link Styles:

#### Solid Link:
```javascript
this.ctx.strokeStyle = link.color || '#666';
this.ctx.lineWidth = 2;
this.ctx.setLineDash([]);
this.ctx.stroke();
```

#### Dashed Link:
```javascript
this.ctx.strokeStyle = link.color || '#666';
this.ctx.lineWidth = 2;
this.ctx.setLineDash([8, 4]); // 8px dash, 4px gap
this.ctx.stroke();
```

#### Arrow Style:
```javascript
// Same as solid but with larger arrowheads
this.ctx.setLineDash([]);
this.ctx.lineWidth = 2;
// Draw arrowheads at both ends (size 12)
```

### Connection Point Rendering:

#### TP (Tap Point) - Device attachment:
```javascript
// Small circle at device edge
this.ctx.beginPath();
this.ctx.arc(tp.x, tp.y, 4, 0, Math.PI * 2);
this.ctx.fillStyle = '#4CAF50'; // Green
this.ctx.fill();
this.ctx.strokeStyle = '#333';
this.ctx.lineWidth = 1;
this.ctx.stroke();

// Label
this.ctx.fillStyle = '#000';
this.ctx.font = 'bold 10px Arial';
this.ctx.fillText('TP-1', tp.x, tp.y - 8);
```

#### MP (Moving Point) - Waypoint:
```javascript
// Purple circle
this.ctx.beginPath();
this.ctx.arc(mp.x, mp.y, 5, 0, Math.PI * 2);
this.ctx.fillStyle = '#9C27B0'; // Purple
this.ctx.fill();
this.ctx.strokeStyle = '#333';
this.ctx.lineWidth = 1;
this.ctx.stroke();

// Label
this.ctx.fillStyle = '#9C27B0';
this.ctx.font = 'bold 10px Arial';
this.ctx.fillText('MP-1', mp.x, mp.y - 10);
```

#### UL Endpoint (Free):
```javascript
// Blue circle (larger, draggable)
this.ctx.beginPath();
this.ctx.arc(endpoint.x, endpoint.y, 6, 0, Math.PI * 2);
this.ctx.fillStyle = '#2196F3'; // Blue
this.ctx.fill();
this.ctx.strokeStyle = '#fff';
this.ctx.lineWidth = 2;
this.ctx.stroke();

// Outer glow when hovered
if (hovered) {
    this.ctx.strokeStyle = 'rgba(33, 150, 243, 0.5)';
    this.ctx.lineWidth = 10;
    this.ctx.stroke();
}
```

### Link Type Labels (Debug Mode):
```javascript
// Show link type above link
if (this.showLinkTypeLabels) {
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;
    
    this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    this.ctx.fillRect(midX - 20, midY - 12, 40, 16);
    
    this.ctx.fillStyle = '#000';
    this.ctx.font = 'bold 11px monospace';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(link.linkType, midX, midY + 3);
}
```

---

## UI SNAPSHOT 7: Text Label Rendering
**File:** `topology.js` (drawText method)
**Description:** Rotatable text labels with edit handles

### Text Rendering:
```javascript
function drawText(textObj) {
    this.ctx.save();
    
    // Apply rotation
    this.ctx.translate(textObj.x, textObj.y);
    this.ctx.rotate(textObj.rotation * Math.PI / 180);
    
    // Draw text
    this.ctx.fillStyle = textObj.color || '#000';
    this.ctx.font = `${textObj.fontSize}px Arial`;
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(textObj.text, 0, 0);
    
    // Selection highlight
    if (textObj === this.selectedObject) {
        const metrics = this.ctx.measureText(textObj.text);
        const width = metrics.width;
        const height = parseInt(textObj.fontSize);
        
        // Blue rectangle around text
        this.ctx.strokeStyle = '#2196F3';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(-5, -height/2 - 5, width + 10, height + 10);
        
        // Rotation handle (circle at right edge)
        const handleX = width + 20;
        const handleY = 0;
        this.ctx.beginPath();
        this.ctx.arc(handleX, handleY, 6, 0, Math.PI * 2);
        this.ctx.fillStyle = '#4CAF50';
        this.ctx.fill();
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // Resize handle (circle at bottom)
        const resizeX = width / 2;
        const resizeY = height / 2 + 20;
        this.ctx.beginPath();
        this.ctx.arc(resizeX, resizeY, 6, 0, Math.PI * 2);
        this.ctx.fillStyle = '#FF9800';
        this.ctx.fill();
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }
    
    this.ctx.restore();
}
```

### Edit Handles:
- **Rotation Handle**: Green circle, drag to rotate
- **Resize Handle**: Orange circle, drag to change font size
- **Selection Box**: Blue rectangle around text
- **Double-click**: Opens inline text editor

---

## UI SNAPSHOT 8: Context Menu
**File:** `index.html` (Context menu div) + `styles.css` (Lines 1000-1100)
**Description:** Right-click menu for quick actions

### Visual Structure:
```
┌─────────────────────┐
│ 📋 Copy             │
├─────────────────────┤
│ 📄 Paste            │
├─────────────────────┤
│ 🔗 Create Link      │
├─────────────────────┤
│ 🎨 Change Color...  │
├─────────────────────┤
│ 🔄 Duplicate        │
├─────────────────────┤
│ ❌ Delete           │
└─────────────────────┘
```

### Styling:
```css
.context-menu {
    position: fixed;
    background: white;
    border: 1px solid #ccc;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 4px 0;
    min-width: 180px;
    z-index: 10000;
}

.context-menu-item {
    padding: 8px 16px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.context-menu-item:hover {
    background: rgba(52, 152, 219, 0.1);
}

.context-menu-item.disabled {
    color: #999;
    cursor: not-allowed;
}

.context-menu-divider {
    height: 1px;
    background: #eee;
    margin: 4px 0;
}
```

### Features:
- Appears at mouse cursor position
- Context-aware items (different for devices/links/text)
- Disabled items shown in gray
- Emoji icons for visual clarity
- Keyboard shortcuts shown on right
- Closes on click outside or Esc key

---

## UI SNAPSHOT 9: Modal Dialogs
**File:** `index.html` (Modal sections) + `styles.css` (Lines 1200-1350)
**Description:** Various dialog boxes for user input

### Advanced Text Editor Modal:
```
┌────────────────────────────────────┐
│  Edit Text                      [X]│
├────────────────────────────────────┤
│  ┌──────────────────────────────┐ │
│  │ Enter your text here...      │ │
│  │                              │ │
│  │                              │ │
│  └──────────────────────────────┘ │
│                                    │
│  Font Size: [14] ▄▄▄▄▄▄▄▄ 72      │
│  Rotation:  [0°] ▄▄▄▄▄▄▄▄ 360°    │
│  Color:     [🎨 #000000]          │
│                                    │
│  [ Preview: Sample Text ]          │
│                                    │
│         [Cancel]  [Apply]          │
└────────────────────────────────────┘
```

### Settings Modal:
```
┌────────────────────────────────────┐
│  Settings                       [X]│
├────────────────────────────────────┤
│  Link Options:                     │
│  ☑ Curve Mode                      │
│  ☑ Continuous Mode                 │
│  ☑ Sticky Mode                     │
│  ☑ Unbound Links (UL)              │
│                                    │
│  Device Options:                   │
│  ☑ Auto-Numbering                  │
│  ☐ Collision Detection             │
│  ☑ Movable Devices                 │
│                                    │
│  Visual:                           │
│  ☐ Dark Mode                       │
│  ☑ Grid Zoom                       │
│  ☐ Show Link Type Labels           │
│                                    │
│  Magnetic Field: [40] ▄▄▄▄▄ 80    │
│                                    │
│              [Close]               │
└────────────────────────────────────┘
```

### Modal Styling:
```css
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10001;
    backdrop-filter: blur(4px);
}

.modal {
    background: white;
    border-radius: 10px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    padding: 20px;
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #eee;
}

.modal-title {
    font-size: 20px;
    font-weight: 600;
    color: #333;
}

.modal-close {
    cursor: pointer;
    font-size: 24px;
    color: #999;
    background: none;
    border: none;
}

.modal-close:hover {
    color: #333;
}
```

---

## UI SNAPSHOT 10: Bottom Bug Alert
**File:** `index.html` (Lines 10-37)
**Description:** Debugging notification system

### Visual Design:
```
┌─────────────────────────────────────────────────┐
│ 🚨 BUG DETECTED [CRITICAL] [RACE_CONDITION]     │
│    Endpoint becomes undefined after detach      │
│    ⚠️ Code Conflicts: 3                         │
│         [📋 Copy]  [Details]  [✕]              │
└─────────────────────────────────────────────────┘
```

### Styling:
```css
#bottom-bug-alert {
    position: fixed;
    bottom: 60px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, 
        rgba(231, 76, 60, 0.98), 
        rgba(192, 57, 43, 0.98));
    color: white;
    padding: 12px 18px;
    border-radius: 10px;
    box-shadow: 0 6px 24px rgba(231, 76, 60, 0.7);
    border: 2px solid rgba(255, 255, 255, 0.2);
    max-width: 700px;
    z-index: 100001;
}

@keyframes pulse-icon {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.1); opacity: 0.8; }
}
```

### Features:
- Red gradient background (critical issues)
- Animated pulsing emoji icon
- Severity badge (CRITICAL/WARNING/INFO)
- Category badge (bug type)
- Code conflict counter
- Copy button for bug report
- Details button jumps to debugger
- Dismiss button
- Auto-position at bottom center

---

## UI SNAPSHOT 11: Zoom Controls
**File:** `index.html` (Zoom section) + `styles.css` (Lines 400-450)
**Description:** Canvas zoom interface

### Visual Layout:
```
┌─────────────────┐
│   Zoom: 100%    │
│  [−]  ▄▄▄  [+] │
│     [Reset]     │
└─────────────────┘
```

### Zoom Indicator:
```javascript
// Update zoom display
function updateZoomDisplay() {
    const zoomPercent = Math.round(this.zoom * 100);
    document.getElementById('zoom-level').textContent = `${zoomPercent}%`;
    
    // Color code zoom level
    const indicator = document.getElementById('zoom-indicator');
    if (this.zoom < 0.5) {
        indicator.style.color = '#FF5722'; // Red (too zoomed out)
    } else if (this.zoom > 2) {
        indicator.style.color = '#FF9800'; // Orange (very zoomed in)
    } else {
        indicator.style.color = '#4CAF50'; // Green (normal)
    }
}
```

### Controls:
- **Zoom In Button** (+): Increases zoom by 10%
- **Zoom Out Button** (−): Decreases zoom by 10%
- **Zoom Slider**: Continuous control (0.25x to 3x)
- **Reset Button**: Returns to 100% zoom and (0,0) pan
- **Percentage Display**: Shows current zoom level
- **Color Coding**: Visual feedback for extreme zoom

---

## UI SNAPSHOT 12: Link Style Selector
**File:** `index.html` (Link table section)
**Description:** Per-link style customization UI

### Style Dropdown:
```
┌──────────────────┐
│ ───── Solid   ▼ │  ← Currently selected
├──────────────────┤
│ ─ ─ ─ Dashed    │
│ ────> Arrow     │
└──────────────────┘
```

### Visual Previews in Dropdown:
```css
.link-style-option {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px;
}

.link-style-preview {
    width: 40px;
    height: 2px;
    background: #666;
}

.link-style-preview.solid {
    background: linear-gradient(to right, #666 100%, #666 100%);
}

.link-style-preview.dashed {
    background: repeating-linear-gradient(
        to right,
        #666 0px,
        #666 8px,
        transparent 8px,
        transparent 12px
    );
}

.link-style-preview.arrow::after {
    content: '→';
    position: absolute;
    right: 0;
    font-size: 16px;
}
```

### Features:
- Visual preview of each style
- Instant apply on selection
- Per-link customization
- Saved with topology
- Default style setting

---

## UI SNAPSHOT 13: Dark Mode Theme
**File:** `styles.css` (Dark mode sections)
**Description:** Complete dark theme styling

### Color Palette:
```css
/* Dark Mode Colors */
--dm-background: #1a1a1a;
--dm-surface: #2a2a2a;
--dm-border: #3a3a3a;
--dm-text-primary: #ffffff;
--dm-text-secondary: #b0b0b0;
--dm-accent: #3498db;
--dm-grid: rgba(255, 255, 255, 0.05);
```

### Component Styling:

#### Canvas:
```css
body.dark-mode canvas {
    background: #1a1a1a;
}

body.dark-mode .grid-line {
    stroke: rgba(255, 255, 255, 0.05);
}
```

#### Panels:
```css
body.dark-mode .properties-panel {
    background: #2a2a2a;
    border-left: 1px solid #3a3a3a;
    color: #ffffff;
}

body.dark-mode .toolbar {
    background: rgba(42, 42, 42, 0.95);
}
```

#### Inputs:
```css
body.dark-mode .property-input {
    background: #333;
    border: 1px solid #444;
    color: #fff;
}

body.dark-mode .property-input:focus {
    border-color: #3498db;
    background: #3a3a3a;
}
```

#### Tables:
```css
body.dark-mode .link-table {
    background: #2a2a2a;
}

body.dark-mode .link-table th {
    background: #333;
    color: #b0b0b0;
}

body.dark-mode .link-table tr:hover {
    background: rgba(52, 152, 219, 0.15);
}
```

### Toggle Button:
```javascript
// Dark mode toggle
function toggleDarkMode() {
    this.darkMode = !this.darkMode;
    document.body.classList.toggle('dark-mode', this.darkMode);
    localStorage.setItem('darkMode', this.darkMode);
    
    // Update icon
    const icon = document.getElementById('dark-mode-icon');
    icon.textContent = this.darkMode ? '☀️' : '🌙';
    
    this.render(); // Redraw with new colors
}
```

---

## UI SNAPSHOT 14: Responsive Layout
**File:** `styles.css` (Media queries)
**Description:** Adaptive design for different screen sizes

### Breakpoints:
```css
/* Large screens (default) */
@media (min-width: 1200px) {
    .properties-panel { width: 300px; }
    .toolbar { width: 70px; }
}

/* Medium screens (tablets) */
@media (max-width: 1199px) {
    .properties-panel { width: 250px; }
    .toolbar { width: 60px; }
    .top-bar { padding: 0 10px; }
}

/* Small screens (mobile landscape) */
@media (max-width: 768px) {
    .properties-panel {
        position: fixed;
        bottom: 0;
        right: 0;
        left: 70px;
        top: auto;
        width: auto;
        height: 200px;
        border-left: none;
        border-top: 1px solid #ddd;
    }
    
    .toolbar {
        width: 50px;
        flex-direction: column;
    }
    
    .tool-btn {
        width: 50px;
        height: 50px;
    }
}

/* Extra small (mobile portrait) */
@media (max-width: 480px) {
    .top-bar {
        height: 40px;
        font-size: 12px;
    }
    
    .toolbar {
        width: 45px;
        top: 40px;
    }
    
    .tool-btn {
        width: 45px;
        height: 45px;
    }
    
    .properties-panel {
        height: 150px;
        font-size: 12px;
    }
}
```

### Touch Optimization:
```css
/* Larger touch targets on mobile */
@media (max-width: 768px) {
    .tool-btn,
    .context-menu-item,
    .link-table td button {
        min-height: 44px; /* iOS recommendation */
        min-width: 44px;
    }
    
    /* Hide some less critical UI on small screens */
    .advanced-features {
        display: none;
    }
}
```

---

## Summary of UI Components

### Main Interface Elements:
1. ✅ **Top Bar Navigation** - File operations and utilities
2. ✅ **Left Toolbar** - Tool palette (select/device/link/text)
3. ✅ **Right Panel** - Properties editor and link table
4. ✅ **Canvas & Grid** - Main drawing area with background grid
5. ✅ **Device Rendering** - Router and switch icons
6. ✅ **Link Rendering** - Connection visualizations with styles
7. ✅ **Text Labels** - Rotatable text with edit handles
8. ✅ **Context Menu** - Right-click quick actions
9. ✅ **Modal Dialogs** - Settings and text editor
10. ✅ **Bug Alert** - Debugging notification system
11. ✅ **Zoom Controls** - Canvas zoom interface
12. ✅ **Link Style Selector** - Per-link style picker
13. ✅ **Dark Mode** - Complete dark theme
14. ✅ **Responsive Layout** - Mobile/tablet adaptation

### Design Principles:
- **Modern UI**: Gradients, shadows, smooth animations
- **Accessibility**: High contrast, large touch targets
- **Consistency**: Unified color scheme and spacing
- **Feedback**: Visual indicators for all interactions
- **Performance**: Hardware-accelerated animations
- **Flexibility**: Toggleable panels, collapsible sections

### Color Scheme (Light Mode):
- Primary: #3498db (Blue)
- Success: #4CAF50 (Green)
- Warning: #FF9800 (Orange)
- Danger: #e74c3c (Red)
- Background: #f5f5f5
- Surface: #ffffff
- Text: #333333

### Color Scheme (Dark Mode):
- Primary: #3498db (Blue)
- Success: #4CAF50 (Green)
- Warning: #FF9800 (Orange)
- Danger: #e74c3c (Red)
- Background: #1a1a1a
- Surface: #2a2a2a
- Text: #ffffff

---

*End of UI/Visual Snapshots*
*Generated: December 5, 2025*




