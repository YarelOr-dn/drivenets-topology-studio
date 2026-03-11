# Topology Creator - Development Guidelines
# ==========================================
# These guidelines document the codebase patterns and rules for development.
# Agents MUST read this file before making changes and UPDATE it after fixes.

## 📁 Key File Locations

| Purpose | Location |
|---------|----------|
| Main topology logic | `topology.js` |
| Styles | `styles.css` |
| HTML entry point | `index.html` |
| Debugger panel | `debugger.js` |
| DNAAS discovery | `dnaas_path_discovery.py` |
| Momentum physics | `topology-momentum.js` |
| History/undo | `topology-history.js` |

---

## 🧩 Modular Architecture

The topology editor uses a modular architecture with wrapper modules that provide clean APIs.

### Module Overview

#### Foundation Layer (load first)
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-errors.js` | ErrorBoundary | `window.ErrorBoundary` | Crash protection & recovery |
| `topology-registry.js` | TopologyRegistry | `window.TopologyRegistry` | **Feature routing - check first!** |
| `topology-events.js` | TopologyEventBus | `editor.events` | Event pub-sub system |
| `topology-geometry.js` | TopologyGeometry | `window.TopologyGeometry` | Math/geometry utilities |
| `topology-platform-data.js` | PlatformData | `editor.platformData` | Platforms & transceivers |

#### Core Layer
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-input.js` | InputManager | `editor.input` | Input state machine |
| `topology-files.js` | FileManager | `editor.files` | Auto-save, crash recovery, session tracking |
| `topology-file-ops.js` | FileOps | `window.FileOps` | Save/load/export, bug topologies, custom sections, clear canvas |
| `topology-drawing.js` | DrawingManager | `editor.drawing` | Canvas rendering |
| `topology-history.js` | HistoryManager | `editor.history` | Undo/redo |

#### Object Managers
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-text.js` | TextManager | `editor.text` | Text handling |
| `topology-shapes.js` | ShapeManager | `editor.shapes` | Shape handling |
| `topology-devices.js` | DeviceManager | `editor.devices` | Device management |
| `topology-links.js` | LinkManager | `editor.links` | Links & BUL chains |

#### UI Layer
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-ui.js` | UIManager | `editor.ui` | Toolbars & panels |
| `topology-menus.js` | MenuManager | `editor.menus` | Context menus |
| `topology-minimap.js` | MinimapManager | `editor.minimapMgr` | Minimap display |
| `topology-link-editor.js` | LinkEditorModal | `editor.linkEditor` | Link details modal |
| `topology-groups.js` | GroupManager | `editor.groups` | Object grouping |
| `topology-toolbar.js` | ToolbarManager | `editor.toolbarMgr` | Toolbar setup |
| `topology-dnaas.js` | DnaasManager | `editor.dnaas` | DNAAS discovery |
| `topology-network-mapper.js` | NetworkMapperManager | `editor.networkMapper` | Recursive LLDP network discovery + auto-layout |

#### Extracted Handlers (Feb 2026 decomposition)
| Module | Global | Purpose |
|--------|--------|---------|
| `topology-context-menu-handlers.js` | `window.ContextMenuHandlers` | Context menus, curve submenus, copy/paste style, layers/device-style submenus |
| `topology-link-details.js` | `window.LinkDetailsHandlers` | Link editor modal, VLAN validation, link details table |
| `topology-shape-methods.js` | `window.ShapeMethods` | Shape creation, hit detection, resize handles, toolbar |
| `topology-selection-popups.js` | `window.SelectionPopups` | Device style palette, link width/style/curve options, LLDP submenu |
| `topology-link-geometry.js` | `window.LinkGeometry` | Link hit detection, distance calculations, BUL chain analysis |
| `topology-text-attachment.js` | `window.TextAttachment` | Text-to-link attachment, nearest link, adjacent text |

#### Mouse Handlers (Feb 2026 decomposition)
| Module | Global | Purpose |
|--------|--------|---------|
| `topology-mouse.js` | `window.MouseHandler` | Thin coordinator - delegates to down/move/up handlers |
| `topology-mouse-down.js` | `window.MouseDownHandler` | Click handling, selection, drag setup, double-tap |
| `topology-mouse-move.js` | `window.MouseMoveHandler` | Drag, link stretch, cursor feedback, collision |
| `topology-mouse-up.js` | `window.MouseUpHandler` | Drag release, link creation, placement, cleanup |

#### Testing
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-tests.js` | TopologyTests | `window.TopologyTests` | Automated test suite |

### Using Modules

All modules use constructor injection and delegate to the main editor:

```javascript
// Modules receive the editor instance
class DeviceManager {
    constructor(editor) {
        this.editor = editor;
    }
    
    // Methods delegate to editor
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'device') || [];
    }
}
```

### Accessing Modules

```javascript
// From editor instance
const editor = window.topologyEditor;

// Device operations
editor.devices.getAll();
editor.devices.addAtPosition('SA-40C', 100, 200);
editor.devices.getById('device-1');

// Link operations
editor.links.getAll();
editor.links.analyzeBULChain(link);
editor.links.isHead(link);

// UI operations
editor.ui.showDeviceToolbar(device);
editor.ui.hideAllToolbars();

// Menu operations
editor.menus.showContextMenu(x, y, obj);
```

### Script Load Order

Modules must load BEFORE `topology.js`:

```html
<!-- Foundation -->
<script src="topology-events.js"></script>
<script src="topology-geometry.js"></script>
<script src="topology-platform-data.js"></script>

<!-- Core Services -->
<script src="topology-files.js"></script>
<script src="topology-file-ops.js"></script>
<script src="topology-drawing.js"></script>

<!-- Object Managers -->
<script src="topology-text.js"></script>
<script src="topology-shapes.js"></script>
<script src="topology-devices.js"></script>
<script src="topology-links.js"></script>

<!-- UI Layer -->
<script src="topology-ui.js"></script>
<script src="topology-menus.js"></script>
<script src="topology-minimap.js"></script>
<script src="topology-link-editor.js"></script>
<script src="topology-groups.js"></script>
<script src="topology-toolbar.js"></script>
<script src="topology-dnaas.js"></script>

<!-- Main (loads last, uses all modules) -->
<script src="topology.js"></script>

<!-- Tests (optional) -->
<script src="topology-tests.js"></script>
```

### Running Tests

```javascript
// Run all tests
TopologyTests.runAll();

// Run specific module tests
TopologyTests.runModule('devices');
TopologyTests.runModule('links');
TopologyTests.runModule('ui');
TopologyTests.runModule('linkeditor');
TopologyTests.runModule('stats');

// View module diagnostics
ModuleStats.print();          // Print formatted stats table
ModuleStats.getSummary();     // Get stats object
ModuleStats.getHealth();      // Get 'healthy', 'degraded', or 'critical'
```

---

## 🔗 BUL (Bound Unbound Link) Chain System

### Core Concepts

**UL (Unbound Link)**: A link not attached to devices at both ends. Has two endpoints: `start` and `end`.

**BUL (Bound Unbound Link)**: Multiple ULs merged together into a chain.

**TP (Terminal Point)**: A FREE endpoint - not attached to device AND not connected to another link.

**MP (Merge Point)**: Where two ULs connect - the shared point between parent and child.

### Merge Relationships

Each link can have:
- `mergedWith`: Points to CHILD link (this link is parent)
- `mergedInto`: Points to PARENT link (this link is child)

**A link can only have ONE child (one `mergedWith`)!**

```
Chain: HEAD -- MP1 -- MIDDLE -- MP2 -- TAIL

HEAD:   mergedWith → MIDDLE,  mergedInto = null
MIDDLE: mergedWith → TAIL,    mergedInto → HEAD  
TAIL:   mergedWith = null,    mergedInto → MIDDLE
```

### Key Properties in mergedWith

```javascript
mergedWith = {
    linkId: 'link_123',           // Child link ID
    connectionPoint: {x, y},       // MP position (CLONED, not shared!)
    connectionEndpoint: 'start',   // Which endpoint of PARENT connects to child
    childConnectionEndpoint: 'end', // Which endpoint of CHILD connects to parent
    parentFreeEnd: 'end',          // Which endpoint of PARENT is FREE
    childFreeEnd: 'start',         // Which endpoint of CHILD is FREE
    mpNumber: 1                    // MP number in chain (MP-1, MP-2, etc.)
}
```

### CRITICAL: Endpoint Detection

Use `isEndpointConnected(link, endpoint)` to check if an endpoint is connected:
- Checks BOTH `mergedWith.connectionEndpoint` AND `mergedInto.childEndpoint`
- Returns `true` if endpoint is an MP (connected to another link)
- Returns `false` if endpoint is a TP (free)

**NEVER use only `device1`/`device2` checks - must also check merge connections!**

```javascript
// CORRECT: Check device AND merge connection
const isStartFree = !link.device1 && !this.isEndpointConnected(link, 'start');

// WRONG: Only checks device
const isStartFree = !link.device1;  // Missing merge check!
```

### Extending from TP (Link-from-TP Mode)

When user clicks a TP to extend the chain:

1. **APPEND** (sourceLink has no child): sourceLink becomes parent of newUL
   - `sourceLink.mergedWith → newUL`
   - `newUL.mergedInto → sourceLink`

2. **PREPEND** (sourceLink already has a child): newUL becomes parent (new HEAD)
   - `newUL.mergedWith → sourceLink`
   - `sourceLink.mergedInto → newUL`

**NEVER overwrite existing `mergedWith` - it breaks the chain!**

### Finding All Links in Chain

```javascript
const allLinks = this.getAllMergedLinks(link);
// Traverses both mergedWith (children) and mergedInto (parents)
// Returns array of all connected links
```

---

## 🎯 Hitbox & Selection Rules

### Link Hit Detection

Use `_checkLinkHit(x, y, obj)` which:
- Calculates visual link width based on zoom
- Uses screen-pixel tolerance for consistent feel
- Returns distance to link (-1 if not hit)

**For BUL chains**: TAIL/MIDDLE links delegate hit detection to HEAD.

### Finding Closest Object

`findObjectAt(x, y)` accumulates ALL links within clicking distance and returns the **closest** one, not just the first found.

### Selection Priority (Visual = Hitbox)

Objects are selected based on visual stacking order: higher-layer objects have priority over lower-layer ones. Within the same layer, priority is: text > device > link > shape. Only `mergedToBackground` shapes are always lowest priority. This ensures "what you see is what you click."

---

## 🎨 UI/Style Conventions

### Device Style Buttons
- Active state: **GREEN** gradient (like "Place Device" button)
- Labels: `white-space: nowrap` - no truncation

### Link Style Buttons  
- Active state: **CYAN** gradient

### Button Text
- "Place Device" (not "Add Device")

### Selection Toolbars (Liquid Glass Design)

**Single left-click** on objects shows floating toolbars (no right-click needed):

| Object | Function | Toolbar ID | Trigger |
|--------|----------|------------|---------|
| Text | `showTextSelectionToolbar(textObj)` | `text-selection-toolbar` | Left-click to select |
| Device | `showDeviceSelectionToolbar(device)` | `device-selection-toolbar` | Left-click to select |
| Link | `showLinkSelectionToolbar(link, clickPos?)` | `link-selection-toolbar` | Left-click to select |

**Toolbar Behavior:**
- Appears 150ms after selection (prevents showing during drag)
- Hidden when: dragging starts, clicking empty space, returning to base mode
- **Re-appears after drag ends** at the new object position
- Call `hideAllSelectionToolbars()` to hide all toolbars programmatically

**Toolbar Positioning:**
- **Device**: Below the device center (like text toolbar)
- **Link**: At the click location (where user clicked on the link)
- **Text**: Below the text center

**Toolbar Design Pattern:**
```javascript
toolbar.style.cssText = `
    position: fixed;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 5px 8px;
    backdrop-filter: blur(20px) saturate(150%);
    display: flex;
    gap: 2px;
`;
```

**Hide All Toolbars:**
```javascript
this.hideAllSelectionToolbars(); // Hides text, device, and link toolbars
```

**Device Toolbar Options:** SSH, Rename, Color, Style, Duplicate, Lock, Delete
- SSH → `handleContextSSHAddress()`
- Rename → `showRenamePopup(device)`
- Color → `showColorPalettePopup(device, 'device')`
- Style → `showDeviceStylePalette(device)`
- Duplicate → `duplicateSelected()`
- Lock → toggle `device.locked`
- Delete → `deleteSelected()`

**Link Toolbar Options:** Add Text, Color, Width, Style, Curve, Duplicate, Delete
- Add Text → `showAdjacentTextMenu(link)`
- Color → `showColorPalettePopup(link, 'link')`
- Width → `showLinkWidthSlider(link)`
- Style → `showLinkStyleOptions(link)`
- Curve → `showLinkCurveOptions(link)`
- Duplicate → `duplicateSelected()`
- Delete → `deleteSelected()`

---

## ✅ Before Making Changes

1. Read this file
2. `grep` for existing patterns in codebase
3. Check related `.md` files for context
4. Read the specific code section before modifying

## ✅ After Making Changes

1. Verify braces are balanced:
   ```bash
   python3 -c "js=open('topology.js').read(); print('✓' if js.count('{')==js.count('}') else '❌')"
   ```
2. Test the change in browser
3. Update this file with new patterns/fixes

---

## 🐛 Recent Fixes (Jan 2026)

### Arrow Tips Drawn On Top of Devices (Mar 1)
**Problem**: Link arrowheads were drawn during the link pass (before devices), so device fills covered the arrow tips, making them invisible.
**Fix**: Arrow geometry/styling is now computed in `drawLink`/`drawUnboundLink` and stored on the link object (`_arrowTipEnd`, `_arrowEndAngle`, `_arrowLength`, `_arrowAngleSpread`, `_arrowFillColor`, etc.). A new `drawLinkArrows()` function in `topology-link-drawing.js` renders them in a dedicated "ARROW TIPS PASS" in `topology-draw.js` that runs after devices and labels.
**Files**: `topology-link-drawing.js`, `topology-draw.js`, `topology.js` (delegation stub).

### Layer-Based Selection Priority (Mar 1)
**Problem**: Objects on higher visual layers were not selected with priority — shapes were always forced to lowest selection priority regardless of layer.
**Fix**: `findObjectAt` in `topology-object-detection.js` now sorts candidates by `layer` (descending) first, then by `typeOrder` (text > device > link > shape) within the same layer. Only `mergedToBackground` shapes retain bottom priority.
**Files**: `topology-object-detection.js`.

### Modular Decomposition (Feb 12)
**Change**: Extracted ~11,000 lines from `topology.js` (17K -> 13.4K) and split `topology-mouse.js` (7.5K -> 33 lines coordinator + 3 handler files).
**New modules**: `topology-context-menu-handlers.js` (1605 lines), `topology-link-details.js` (671), `topology-shape-methods.js` (464), `topology-selection-popups.js` (522), `topology-link-geometry.js` (523), `topology-text-attachment.js` (337), `topology-mouse-down.js` (2538), `topology-mouse-move.js` (2775), `topology-mouse-up.js` (1985).
**Pattern**: Each extracted method receives `editor` as first parameter instead of using `this`. Stubs in topology.js delegate via `if (window.ModuleName) return window.ModuleName.method(this, ...args);`
**Load order**: New modules load BEFORE `topology.js` via `<script>` tags in `index.html`.

### Seamless Object-to-Object Toolbar Transition (Feb 12)
**Problem**: Clicking from one device to another caused the old toolbar to linger for 150ms before being replaced, making transitions feel janky.
**Root cause**: `hideAllSelectionToolbars()` was only called when clicking empty grid, not when clicking a different object. The 150ms toolbar delay was the same for first selection and transitions.
**Fix (topology-mouse.js)**:
1. Added `editor.hideAllSelectionToolbars()` immediately in the `!alreadySelected` path (line ~1230), so the old toolbar disappears instantly when clicking a new object.
2. Introduced `hadPreviousSelection` flag to use a shorter toolbar delay (50ms) when transitioning between objects vs. first selection from empty (150ms).
**Result**: Old toolbar vanishes instantly → 50ms pause → new toolbar appears. All object types (device, link, text, shape) benefit.

### Syntax Error in topology-mouse.js (Feb 12)
**Problem**: Duplicate closing code (lines 7515-7520) caused `SyntaxError: Unexpected token '}'`, preventing `window.MouseHandler` from loading. All canvas clicks silently failed.
**Fix**: Removed the duplicate `}`, `},`, `};`, and `console.log` lines at the end of the file.

### TB+Shape Group Jump, Copy Style from TB, CS Cancel (Feb 10)
**TB+Shape jump**: When text box and shape are grouped and dragged, they jumped. Root cause: momentum was not stopped before capturing positions when expanding group selection. Fix: Call momentum.stopAll() and reset() in the group expand path (topology-mouse.js, topology-groups.js) before building multiSelectInitialPositions.

**Copy Style from TB**: Text toolbar Copy Style only set copiedStyle but never pasteStyleMode=true, so click-to-paste didn't work. Fix: Call editor.copyObjectStyle(textObj) instead of manually setting copiedStyle.

**Copy Style cancel**: Added toast on paste-mode entry: "Click objects to paste. Press Escape to cancel." Added toast on exit: "Copy Style cancelled". Escape already cancelled; now it's discoverable.

**Copy Style cross-type rules** (in `_applyStyleToObject`):
| Source → Target | Color mapping | Other |
|---|---|---|
| Device → TB | device.color → TB bg (if has bg) or text; device.labelColor → TB text | font props |
| TB → Device | TB bg → device.color; TB text → device.labelColor | font props |
| TB → Link | TB bg → link.color (if has bg); else TB text → link.color | TB borderStyle → link style; TB borderWidth → link width |
| Link → TB | link.color → TB bg (if has bg) or text | link style → TB borderStyle |
| TB → Shape | TB bg → shape.fill; TB border/text → shape.stroke (if has bg); else text → both | TB borderWidth → stroke width |
| Shape → TB | shape.fill → TB bg (if has bg) or text; shape.stroke → TB border | shape strokeWidth → TB borderWidth |
| Same-type | full property copy | all applicable props |

**Per-TB `alwaysFaceUser`**: Link-attached TBs can toggle `alwaysFaceUser = true` to stay horizontal (readable) regardless of link angle. The drawing code (`topology-canvas-drawing.js` line ~725) checks `text.alwaysFaceUser === true` and forces 0° rotation. This property is preserved in Copy Style (TB→TB) and shown as an eye/eye-off button in the text selection toolbar for link-attached TBs.

### Group Drag: Jump Fix + BUL Restriction (Feb 10, refined Feb 11)
**Problem**: Grouped objects (TB+shape) jump when grabbed and moved.
**Root cause (FINAL)**: Normal selection path in handleMouseDown did NOT expand groups causing dragStart offset/absolute mismatch. Also stale positions and pointer+mouse double events.
**Fix (3 layers)**: (a) ALL mousedown paths expand groups with isMultiSelect. (b) Threshold handler re-captures FRESH positions. (c) Safety net in handleMouseMove fixes dragStart. 8ms dedup timer.
**RULE**: dragStart for multi-select = ABSOLUTE mouse pos. For single-object = OFFSET. Never mix.

**Problem 2**: Merged (BUL) shapes grouped with devices/shapes - moving fails silently.
**Fix**: Before starting group/multi-select drag, check if selection has both BUL links and other objects (device, shape, text). If so, block drag and show toast: "BUL chains grouped with devices/shapes cannot be moved together. Ungroup first, or move each separately."

### Left-Click Selection Toolbars (Jan 12)
**Change**: Toolbars now appear on **single left-click** (selection), not just right-click.

**Trigger:** Left-click to select any object → toolbar appears after 150ms delay
**Hidden when:** Dragging, clicking empty space, or returning to base mode

**Positioning:**
- Device toolbar: Below device center
- Link toolbar: At click location (passed via `clickPos` parameter)
- Text toolbar: Below text center

**Code Pattern:**
```javascript
// In handleMouseDown - after selection:
setTimeout(() => {
    if (this.selectedObject === clickedObject && !this.dragging) {
        if (clickedObject.type === 'text' && !this._inlineTextEditor) {
            this.showTextSelectionToolbar(clickedObject);
        } else if (clickedObject.type === 'device') {
            this.showDeviceSelectionToolbar(clickedObject);
        } else if (clickedObject.type === 'link' || clickedObject.type === 'unbound') {
            this.showLinkSelectionToolbar(clickedObject);
        }
    }
}, 150);
```

### Selection Toolbars - Liquid Glass Design (Jan 12)
**Change**: Replaced traditional right-click context menus with floating liquid glass toolbars.

**New Functions:**
- `showDeviceSelectionToolbar(device)` - SSH, Rename, Color, Style, Lock, Delete
- `showLinkSelectionToolbar(link)` - Add Text, Color, Width, Style, Curve, Delete
- `hideAllSelectionToolbars()` - Hides all toolbars at once

### BUL Extension from TP Bug (Fixed)
**Problem**: Clicking TP to extend chain would create duplicate TP at MP location.

**Root Causes**:
1. `isFreeTP` only checked device attachment, not merge connections
2. Code overwrote `mergedWith` when extending, breaking existing chain

**Fix**:
1. Use `isEndpointConnected()` in `isFreeTP` check
2. Implement PREPEND vs APPEND logic - if sourceLink has child, new link becomes HEAD

### Device Style Button Names (Fixed)
**Problem**: Names truncated ("Cl...", "C...", etc.)

**Fix**: Added `white-space: nowrap; overflow: visible` to `.style-label`

### Refresh (R / Cmd+R) Without Save-As Suggestion (Fixed)
**Problem**: Refreshing the app via **R** or **Cmd+R** could show "Save As..." (File menu) or browser "Leave site?" dialog.

**Fix**:
1. **No `beforeunload` handler** – Removed from `topology.js` and `bundle.js`. Auto-save already persists to localStorage; a handler triggers browser dialogs.
2. **R and Cmd+R/Ctrl+R handled in-app** – In `handleKeyDown`: `preventDefault()`, `stopPropagation()`, close File dropdown (`#file-dropdown-menu`), then `window.location.reload()`. Ensures no menu or save-as suggestion appears on refresh.

**Files**: `topology.js`, `bundle.js`. See `REMOVE_REFRESH_PROMPT_FIX.md` for details.

---

## 🚫 NEVER DO

1. ❌ Set `mergedWith` without checking if link already has a child
2. ❌ Check only `device1`/`device2` for free endpoint (must also check merges)
3. ❌ Share `connectionPoint` objects between mergedWith and mergedInto (CLONE them!)
4. ❌ Modify code without reading it first
5. ❌ Forget to update this file after fixes
6. ❌ Add a `beforeunload` handler that prompts or forces save on refresh (causes "Leave site?" / save-as suggestion)

## ✅ ALWAYS DO

1. ✅ Use `isEndpointConnected()` to check if endpoint is free
2. ✅ Clone connection points: `{ x: point.x, y: point.y }`
3. ✅ Handle both PREPEND and APPEND scenarios for chain extension
4. ✅ Verify braces balance after edits
5. ✅ Update DEVELOPMENT_GUIDELINES.md after successful fixes
6. ✅ Check `TopologyRegistry.whereDoesThisBelong()` before adding new features
7. ✅ Wrap critical operations with `ErrorBoundary`
8. ✅ Run `TopologyTests.runAll()` after changes

---

## 📋 Feature Templates

### Using the Registry

Before adding new features, check the registry:

```javascript
// In browser console:
TopologyRegistry.whereDoesThisBelong("add alignment tool")
// Returns: { action: 'edit', file: 'topology-input.js', module: 'input', reason: '...' }

// Generate code template:
TopologyRegistry.generateTemplate('objectManager', 'Annotation')
TopologyRegistry.generateTemplate('modal', 'Settings')
TopologyRegistry.generateTemplate('integration', 'Monitor')
```

### Template: New Object Manager```javascript
// topology-{thing}.js
class {Thing}Manager {
    constructor(editor) {
        this.editor = editor;
        this.items = [];
        console.log('{Thing}Manager initialized');
    }
    
    // CRUD operations
    create(options) {
        const item = { id: Date.now(), type: '{thing}', ...options };
        this.items.push(item);
        this.editor.events?.emit('{thing}:created', item);
        this.editor.saveState?.();
        return item;
    }
    
    getAll() { return this.items; }
    getById(id) { return this.items.find(i => i.id === id); }
    remove(id) {
        this.items = this.items.filter(i => i.id !== id);
        this.editor.events?.emit('{thing}:removed', { id });
    }
    
    // Spatial query
    findAt(x, y) {
        return this.items.find(item => /* hit test */);
    }
    
    // Drawing
    draw(ctx, item) {
        // Render the item
    }
}

window.{Thing}Manager = {Thing}Manager;
window.create{Thing}Manager = (editor) => new {Thing}Manager(editor);
```

### Template: New Input State

```javascript
// Add to topology-input.js
class {Mode}Handler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = '{mode}';
    }
    
    enter(context = {}) {
        super.enter(context);
        this.editor.canvas.style.cursor = 'crosshair';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        super.exit();
    }
    
    onMouseDown(e) { return null; } // null = stay, 'idle' = exit
    onMouseMove(e) { return null; }
    onMouseUp(e) { return 'idle'; }
    onKeyDown(e) { if (e.key === 'Escape') return 'idle'; return null; }
}

// Register: inputManager.registerState('{mode}', new {Mode}Handler(editor, inputManager));
```

### Template: New Modal

```javascript
// topology-{name}-modal.js
class {Name}Modal {
    constructor(editor) {
        this.editor = editor;
        this.element = null;
        this.isVisible = false;
    }
    
    show(data = {}) {
        this.data = data;
        this.createModal();
        this.populateFields();
        this.isVisible = true;
    }
    
    hide() {
        if (this.element) {
            this.element.remove();
            this.element = null;
        }
        this.isVisible = false;
    }
    
    createModal() {
        this.element = document.createElement('div');
        this.element.className = '{name}-modal-overlay';
        this.element.innerHTML = `
            <div class="{name}-modal">
                <div class="modal-header"><h2>{Name}</h2><button class="close">&times;</button></div>
                <div class="modal-body"><!-- fields --></div>
                <div class="modal-footer"><button class="cancel">Cancel</button><button class="save">Save</button></div>
            </div>
        `;
        document.body.appendChild(this.element);
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.element.querySelector('.close')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.cancel')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.save')?.addEventListener('click', () => this.save());
    }
    
    save() { /* validate and save */ this.hide(); }
}

window.{Name}Modal = {Name}Modal;
```

---

## 🛡️ Error Handling Patterns

### Wrapping Event Handlers

```javascript
// Use ErrorBoundary for crash protection
const safeHandler = ErrorBoundary.wrapEventHandler(
    (e) => this.handleClick(e),
    this,
    'click'
);
this.canvas.addEventListener('click', safeHandler);
```

### Safe Module Initialization

```javascript
// In topology.js constructor
this.myModule = ErrorBoundary.safeModuleInit('ModuleName',
    () => new MyModule(this),
    () => ({ /* fallback object */ })
);
```

### Auto-Save and Crash Recovery

```javascript
// Enable auto-save (30 second interval)
this.files.enableAutoSave();

// Check for recovery on startup
this.files.checkForRecovery();
```

**Recovery skip conditions** (won't show dialog):
1. Previous session closed cleanly (`beforeunload` → `markSessionClosed()`)
2. Recovery data matches the last saved topology (`topology_current` in localStorage)
3. `quickSaveTopology()` syncs recovery data session ID to current session

### File Menu

The File button (`#btn-file-menu`) in the top bar opens `#file-dropdown-menu` positioned
directly below the button (not centered). Wired in `topology-toolbar-setup.js`.
Close handlers: outside-click + Escape (inline script in `index.html`).

### File Upload

`loadTopology(event)` in `topology.js` reads via `FileReader`, handles wrapped formats
(`{topology: {objects}}`, bare arrays), and resets the file input for re-selection.

---

## 🧪 Testing Checklist

After any code change:

```javascript
// Run all tests
TopologyTests.runAll()

// Run specific module tests
TopologyTests.runModule('devices')
TopologyTests.runModule('links')
TopologyTests.runModule('input')
```

Manual testing:
- [ ] Feature works as expected
- [ ] Selection still works
- [ ] Undo/Redo still works
- [ ] Save/Load still works
- [ ] No console errors
6. ✅ Handle R and Cmd+R/Ctrl+R for refresh in `handleKeyDown` (preventDefault, close file menu, reload) so no save-as appears

---

## Debug-DNOS Topology Integration

The topology app integrates with `/debug-dnos` bug evidence system:

### Backend (`serve.py`)

- `GET /debug-dnos-topologies/list.json` — scans `~/SCALER/FLOWSPEC_VPN/bug_evidence/*.topology.json` and returns a JSON list
- `GET /debug-dnos-topologies/<filename>` — serves a specific `.topology.json` file

### Frontend (`topology.js` + `index.html`)

- "Topologies" dropdown has a "Debug-DNOS Topologies" section (red accent)
- `showDebugDnosTopologiesSubmenu()` fetches the list
- `showDebugDnosTopologySelector(topologies)` shows a modal picker
- `loadDebugDnosTopology(filename)` fetches and loads into the canvas

### Topology JSON Visual Standards (for generated files)

**Pre-creation checklist (mandatory):**

- Identify the PRIMARY bug (not secondary effects). Re-read the `.md` Expected/Actual sections first.
- VRF panel text must use `show` command language (e.g., "Redirect target: selected"), NOT code internals (e.g., "BGP_CONFIG_RD not set").
- For comparison bugs: both panels show what differs and the result from the user's perspective.
- Scan JSON for code-level leakage (function names, file names, protobuf fields) — remove any.

**Visual rules:**

1. Device labels = name only; IP as separate TB below (`y = device_y + radius + 30`)
2. Every link has a transparent protocol label at midpoint (`_onLinkLine: true`)
3. VRF info uses rectangle shapes as containers with text on top
4. Route info box near ExaBGP with "Route Injected:" header
5. No "BUG:" labels, no code-level details
6. Z-order: Devices → Links → Container shapes → Text → Marker shapes (cross/checkmark LAST)

---

## UI / Branding Notes (Feb 2026)

### Left Toolbar
- **TEXT ACTIVE hidden**: `#text-mode-indicator` is hidden via CSS (user request). Tool mode indicators for Device/Shape/Link remain visible.
- **Shape Type Grid**: `.shape-type-grid` and `.shape-type-btn` provide scalable, aligned layout for the SHAPER section. Use `minmax(0, 1fr)` for responsive columns.
- **Section alignment**: Toolbar section headers use `min-height: 40px`, `gap: 8px`. Nested subsection headers use `min-height: 28px`. Device/link/font grids use `minmax(0, 1fr)` for equal column sizing.

### XRAY GUI Integration (Feb 2026)

**Overview**: Links between two devices show a magnifying glass icon when selected. Clicking opens an XRAY Capture popup for DP/CP/DNAAS-DP traffic capture, with results delivered to Mac Wireshark.

**Key files:**
- `topology-xray-popup.js` — XRAY popup UI (mode, duration, output, POV, start/stop)
- `topology-link-drawing.js` — Magnifying glass icon drawn at link midpoint (`_getXrayIconPos()`)
- `topology-object-detection.js` — `checkXrayIconHover()`, XRAY icon click detection via `_xrayIconClicked`
- `topology-mouse-down.js` — Routes XRAY icon clicks to `XrayPopup.show()`
- `serve.py` — `/api/xray/run`, `/api/xray/status/{id}`, `/api/xray/stop/{id}`, `/api/xray/config`, `/api/xray/verify-mac`
- `scaler-gui.js` — `openXraySettings()` in CONFIG menu (Mac IP, credentials, Wireshark path)
- `topology-link-details.js` — `autoFillFromLldp()` cross-references LLDP to auto-bind interfaces

**Data flow:**
1. Link selected between 2 devices -> magnifying glass icon drawn at midpoint
2. Click icon -> `XrayPopup.show()` opens floating popup
3. User picks mode/duration/output/POV -> "Start Capture"
4. `POST /api/xray/run` -> `serve.py` runs `live_capture.py` as subprocess
5. Popup polls `GET /api/xray/status/{id}` for progress
6. Mac delivery: SCP pcap + SSH open Wireshark (credentials from `~/.xray_config.json`)

**Editor state:**
- `editor._hoveredXrayIcon` — link whose XRAY icon is hovered (cursor: pointer)
- `editor._xrayIconClicked` — link whose icon was just clicked (consumed in mouse-down)
- `editor._xrayCapturing` — link ID with active capture (pulsing orange ring)
- `link._xrayIconPos` — `{x, y, r}` stored after drawing for hit detection

**Settings:** SCALER CONFIG menu -> "XRAY Settings" -> `openXraySettings()` reads/writes `~/.xray_config.json` via `/api/xray/config`.

### Brand Assets
- **LingoApp**: Official DriveNets brandbook is at https://www.lingoapp.com/110100/k/d5jKxQ — requires LingoApp login to download. Cannot be fetched programmatically.
- **Local branding**: Use `CURSOR/branding/` PDFs (fetched from Mac) for color/logo reference. Extracted logos in `branding/extracted/`.

### Brand Integration (DriveNets)
- **Logo**: Top-bar SVG in `index.html` — three horizontal capsule bars + diagonal slash (DriveNets symbol). Favicon: `branding/extracted/OUR_LOGO_p1_i5_180x180.png`.
- **Icon mapping** (SVG symbols in `index.html`):
  - `ico-router` — DriveNets Routers (rounded rect with 4 crossing arrows + arrowhead tips). Used: Device section header, context menus, Place Device.
  - `ico-dn-switch` — DriveNets Network Switch (rect with converging lines/arrows).
  - `ico-dn-chassis` — DriveNets Network Chassis (rect with vertical slots).
  - `ico-dn-cloud` — DriveNets Cloud (cloud outline).
  - `ico-dn-server` — DriveNets Server/Storage (stacked rack units with indicator dots + stand).
  - `ico-dn-tower` — DriveNets Cell Tower (tower with signal arcs).
  - `ico-dn-firewall` — DriveNets Firewall (shield with grid lines).
  - `ico-globe` — Wireframe globe. Used: curve mode "Use Global Setting".
  - `ico-discover` — Network Operations (cloud with nodes). Used: DNAAS discovery.
  - `ico-network` — Branch (building with peaked roof). Used: network-related UI.
- **Topologies button icon**: `#topo-btn-icon` — layer stack SVG updated dynamically by `FileOps._updateTopoBtnIcon()` to show domain colors on each layer.
- **Button active states**: DNAAS (`.dnaas-panel-open`), Network Mapper (`.nm-panel-open`), and Topologies (`.topologies-open`) buttons retain their base glass appearance with only a highlighted outline glow when open.
- **Topology indicator transitions**: `updateTopologyIndicator()` uses fade+slide animation when switching between topologies.
- **Extraction scripts**:
  - `branding/extract_images.py` — extract images from all brand PDFs.
  - `branding/extract_icon_svgs.py` — crop individual icon PNGs from Drivenets Icons PDF (grid crop) and export full-page SVGs for pages 2–3. Run: `python3 extract_icon_svgs.py`. Output: `branding/extracted/icons/` (300 PNGs), `branding/extracted/icons_page*_full.svg`.

### Backend API Reliability (Mar 2026)

**Request chain**: Browser JS -> serve.py:8080 (proxy) -> discovery_api.py:8765 -> NetworkMapperClient (SSE) -> MCP Server

**Improvements:**
- **LLDP proxy**: `topology-lldp-dialog.js` routes via `/api/dnaas/*` (relative URLs) so it works when deployed to h263; no direct port 8765 calls.
- **MCP session reuse**: `network_mapper_client.py` caches SSE sessions (120s TTL) to avoid 5s handshake per tool call.
- **MCP singleton**: `discovery_api.py` uses `_get_mcp_client()` instead of per-request `NetworkMapperClient()`.
- **Proxy retry**: `serve.py` uses 30s timeout for GET, 300s for POST; 1 retry with 2s backoff on connection errors; 502 includes endpoint and detail.
- **Job cleanup**: `_nm_cleanup_old_jobs()` and `_cleanup_old_discovery_jobs()` remove completed jobs older than 30 minutes.
- **Error feedback**: LLDP dialog shows API/SSH/MCP-specific errors; Network Mapper shows toast after 3 poll failures; DNAAS distinguishes API-down vs SSH vs timeout.

### LLDP Animation & Dialog Fixes (Mar 2026)

**Root causes fixed:**
- **TB disappearing during LLDP enable**: `_drawCanvasWaveDots` and `_drawPulsingGlow` had no delegation in `topology.js` and used `editor` as a free variable. The TypeError crashed inside `ctx.save()` without `ctx.restore()`, corrupting canvas state and hiding all subsequent objects (TBs, text). Fixed by adding delegations and passing `editor` as first parameter.
- **No link animation**: Same root cause -- wave dots along connected links never rendered because `editor._drawCanvasWaveDots()` was undefined. Fixed with the delegation.
- **Table format inconsistency**: Initial LLDP load used 300+ lines of inline table HTML while refresh used `_buildLldpTableHtml`. These drifted apart (different grouping, colors, field name priorities). Fixed by unifying both paths through `updateLldpContent` -> `_buildLldpTableHtml`. Also added missing Port Mirror and Snake group support to `_buildLldpTableHtml`.
- **Safety**: Added try-catch around `_drawLldpEffects` in canvas drawing to prevent canvas corruption on future errors.

### Network Mapper (Mar 2026)

**Overview**: Recursive LLDP-based network discovery that auto-generates debug-dnos-quality topology diagrams from live devices. Supports up to 200 devices with hybrid hierarchical/force-directed auto-layout.

**Key files:**
- `topology-network-mapper.js` — Frontend module: panel UI, discovery control, hybrid layout, rich topology generation, save to domain
- `discovery_api.py` — Backend: `_nm_bfs_crawl()` BFS engine with DNAAS/canvas-aware resolution, MCP enrichment, `/api/network-mapper/start|status|stop` endpoints
- `serve.py` — Proxy `/api/network-mapper/*` to discovery_api.py

**Data flow:**
1. User opens Mapper panel (top-bar button or `N` key), enters seed device IP(s)
2. Frontend collects canvas devices with SSH config as `known_devices`
3. "Start Discovery" → `POST /api/network-mapper/start` with seeds, credentials, limits, known_devices
4. Backend resolves neighbors using known_devices first (DNAAS-aware), then DNS/SCALER DB/inventory
5. MCP path enriches with `get_device_system_info` + `get_device_interfaces_detail` (system_type, version, serial, interface speeds)
6. SSH path collects hostname, serial, system_type, DNOS version, LLDP, mgmt IP, interface brief
7. Frontend polls `GET /api/network-mapper/status?job_id=X` every 2s for live progress
8. On completion, "Generate Topology" creates debug-dnos-quality topology with:
   - Properly styled devices (visualStyle: classic/server/simple, role-based colors)
   - IP address labels below each device
   - System info panels above devices (system_type, version, serial)
   - Color-coded links by interface type (bundle-ether green, ge400 blue, hu400 orange)
   - Interface labels on-link in debug-dnos style
   - SSH config embedded for immediate SCALER use
9. "Save" stores to "Network Mapper" domain (auto-created section, color `#06b6d4`, icon `wifi`)

**Discovery sources (priority order):**
1. Canvas/DNAAS known devices — used for neighbor resolution and credentials
2. Network Mapper MCP (`get_device_lldp` + `get_device_system_info` + `get_device_interfaces_detail`) — enriched
3. SSH (`show system`, `show lldp neighbors`, `show interfaces management`, `show interfaces brief`) — full fallback
4. Device inventory / SCALER DB — for hostname-to-IP resolution

**Device classification (tier → visual):**
| Role | Tier | visualStyle | Color | Radius |
|------|------|-------------|-------|--------|
| NCM/superspine | 0 (top) | server | #c0392b | 50 |
| spine/NCC/RR | 0 (top) | server/classic | #9b59b6 | 50/40 |
| NCF/PE/router | 1 (mid) | classic | #3498db | 40 |
| CE/customer | 2 (bot) | simple | #2ecc71 | 30 |
| external/tester | 2 (bot) | server | #e67e22 | 30 |

**Link styling:**
| Interface | Color | Width | Style |
|-----------|-------|-------|-------|
| bundle-ether | #2ecc71 | 3 | solid |
| hu400/ce400 | #e67e22 | 2 | solid |
| ge400 | #85c1e9 | 2 | solid |
| mgmt | #95a5a6 | 1 | dashed |

**Auto-layout (hybrid):**
- Tier detection from `system_type` and hostname patterns
- If 2+ tiers: hierarchical Y by tier (250px spacing), force-directed X within tier
- If 1 tier: pure force-directed (repulsion + attraction + gravity, 500 max iterations)
- Minimum device spacing: 150px within tier, 180px in force-directed

**Editor state:**
- `editor.networkMapper` — NetworkMapperManager instance
- `editor.networkMapper._jobId` — active discovery job
- `editor.networkMapper._lastDiscoveryData` — latest discovery result (devices with interfaces, links)
- `editor.networkMapper._discoveryCredentials` — {username, password} used for SSH config on generated devices

**Panel UI:**
- Button: `#btn-network-mapper`, keyboard shortcut `N`
- Panel: `#network-mapper-panel` (liquid glass, cyan accent `#06b6d4`)
- Mutual exclusion with DNAAS panel and Topologies dropdown
- States: `.nm-panel-open`, `.nm-running` (spinning icon + pulse), `.nm-complete` (checkmark badge)

---

## Slash Command Knowledge Stores

For Cursor slash-command docs and learning stores in `~/.cursor/commands/`, `~/.cursor/*-reference/`,
`~/.cursor/*-docs/`, and `~/.cursor/skills/`:

- **Agent-facing knowledge should be tiered Markdown**:
  - `learned_index.md` = always-read compact summary (includes `Last synced:` timestamp)
  - `learned_rules.md` = detailed rules, read matching sections only
- **JSON remains the machine-compatible backing store** for tools and scripts. Do not break existing JSON readers unless you are also updating the tooling.
- **Staleness detection** (MANDATORY before reading any index):
  - Run `python3 ~/.cursor/tools/prune_learning.py --command <name> --check`
  - Exit code 0 = fresh, exit code 1 = stale (JSON is newer than mirror)
  - If stale, run `--sync-only` BEFORE trusting the index content
- **After any JSON write-back**, sync is MANDATORY (not optional):
  - `python3 ~/.cursor/tools/prune_learning.py --command <name> --sync-only`
  - Skipping this means subsequent reads use outdated rules
- **Auto-sync mode** for bulk operations:
  - `python3 ~/.cursor/tools/prune_learning.py --command all --auto-sync` syncs only stale stores
- **Backup-before-repair**: if a JSON file is malformed, the tool writes a `.bak` copy before
  attempting regex repair, then writes the repaired JSON back. No silent data loss.
- **Large methodology docs must be split** into:
  - a small TOC / quick-reference `SKILL.md` with a Learning Routing Table
  - targeted `sections/*.md` files loaded on demand
- **Command specs must follow the same reading protocol**:
  - always check freshness first (`--check`)
  - read the compact index / TOC
  - then load only the matching detail sections for the current mode or symptom
- **Self-learning has two paths**:
  - JSON-backed commands (BGP, XRAY, SPIRENT, HA, NETCONF): write to JSON, then MANDATORY sync
  - Direct-Markdown commands (/debug-dnos): edit the correct section file per the Learning Routing Table in SKILL.md