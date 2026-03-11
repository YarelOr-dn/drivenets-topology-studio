# Topology Application Optimization Plan

**Created**: 2026-02-04  
**Current `topology.js` Size**: 20,885 lines  
**Target**: < 5,000 lines (thin orchestration layer)

---

## Executive Summary

The topology application has been undergoing modular refactoring. This plan outlines the remaining complex optimizations needed to achieve a maintainable, crash-immune architecture.

---

## Current File Structure

| File | Lines | Purpose |
|------|-------|---------|
| `topology.js` | 20,885 | Main orchestrator (needs shrinking) |
| `topology-mouse.js` | 7,358 | Mouse event handling |
| `topology-link-drawing.js` | 2,087 | Link rendering |
| `topology-draw.js` | 1,102 | Main draw loop |
| `topology-link-editor.js` | ~2,172 | Link details modal |
| `topology-device-toolbar.js` | 367 | Device selection toolbar |
| `topology-link-toolbar.js` | 424 | Link selection toolbar |
| `topology-minimap.js` | 339 | Minimap navigation |
| `topology-scrollbars.js` | 199 | Scrollbar setup/update |
| `topology-interfaces.js` | 357 | Interface generation |
| `topology-link-popups.js` | 613 | Link popup UIs |
| `topology-color-popups.js` | 360 | Color palette popups |
| `topology-math-utils.js` | 170 | Math utilities |
| `topology-bul-utils.js` | 201 | BUL utility functions |

---

## Phase 1: High-Impact Extractions (Priority)

These extractions will have the biggest impact on reducing `topology.js` size.

### 1.1 DNAAS Module (~2,500 lines)
**Lines**: ~18627-20445  
**Functions to extract**:
- `loadPredefinedDnaasTopology()`
- `isDnaasRouter()`
- `isTerminationDevice()`
- `populateDnaasSuggestions()`
- `showDnaasTraceDialog()`
- `showDnaasFindBDsDialog()`
- `showDnaasInventoryDialog()`
- `showDnaasPathDevicesDialog()`
- `enrichTerminationDevicesWithManagedConfig()`
- `applyDnaasHierarchicalLayout()`
- `loadDnaasData()`
- BD legend methods: `showBDLegend()`, `toggleBDVisibility()`, `setBDVisibilityAll()`, etc.

**Target file**: `topology-dnaas-operations.js`  
**Estimated reduction**: 2,000+ lines

### 1.2 Context Menu Module (~1,500 lines)
**Lines**: ~1925-2230, 6803-8000, 11905-12700  
**Functions to extract**:
- `handleContextMenu()`
- `showBackgroundContextMenu()`
- `showBulkContextMenu()`
- `showMarqueeContextMenu()`
- `showContextMenu()`
- `handleContext*()` methods (CopyStyle, Duplicate, AddText, ToggleCurve, etc.)

**Target file**: `topology-context-menus.js`  
**Estimated reduction**: 1,500 lines

### 1.3 Touch Handling Module (~500 lines)
**Lines**: ~2638-2900  
**Functions to extract**:
- `handleTouchStart()`
- `handleTouchMove()`
- `handleTouchEnd()`
- `process3FingerTap()`
- Touch-related state management

**Target file**: `topology-touch.js`  
**Estimated reduction**: 500 lines

### 1.4 Text Editor Module (~800 lines)
**Lines**: ~7317-7978  
**Functions to extract**:
- `showTextEditor()`
- `showInlineTextEditor()`
- `showInlineDeviceRename()`
- Text toolbar methods
- `applyTextEditor()`

**Target file**: `topology-text-editor.js`  
**Estimated reduction**: 800 lines

---

## Phase 2: Medium-Impact Extractions

### 2.1 Device Editor Module (~600 lines)
**Functions to extract**:
- `showDeviceEditor()`
- `showDeviceStylePalette()`
- `applyDeviceRadius()`
- `applyDeviceLabel()`
- Device-related dialogs

**Target file**: `topology-device-editor.js`  
**Estimated reduction**: 600 lines

### 2.2 Link Editor Extensions (~500 lines)
**Functions to extract**:
- `showLinkWidthSlider()` (already delegating)
- `showLinkStyleOptions()` (already delegating)
- `showLinkCurveOptions()` (already delegating)
- `showLinkDetails()`
- `showLinkInterfaceMenu()`

**Target file**: Enhance `topology-link-popups.js`  
**Estimated reduction**: 500 lines

### 2.3 Wheel/Zoom Module (~300 lines)
**Functions to extract**:
- `handleWheel()`
- `updateZoomIndicator()`
- Zoom-related calculations

**Target file**: `topology-zoom.js`  
**Estimated reduction**: 300 lines

---

## Phase 3: Architectural Improvements

### 3.1 Event Bus Integration
Create a central event bus for inter-module communication:
- Modules emit events instead of direct method calls
- Reduces tight coupling between components
- Enables easier testing

### 3.2 State Management
Centralize state management:
- Extract `objects` array to managed store
- Create computed properties for devices, links, text, shapes
- Enable efficient updates and caching

### 3.3 Input State Machine
Convert input handling to proper state machine:
- States: idle, dragging, linking, selecting, panning, resizing
- Clean transitions between states
- Prevents conflicting interactions

---

## Implementation Order

| Priority | Task | Lines Saved | Complexity |
|----------|------|-------------|------------|
| 1 | DNAAS Operations Module | ~2,000 | Medium |
| 2 | Context Menus Module | ~1,500 | Medium |
| 3 | Text Editor Module | ~800 | Low |
| 4 | Touch Handling Module | ~500 | Low |
| 5 | Device Editor Module | ~600 | Medium |
| 6 | Link Editor Extensions | ~500 | Low |
| 7 | Zoom Module | ~300 | Low |

**Total potential reduction**: ~6,200 lines

**Projected `topology.js` size after Phase 1+2**: ~14,500 lines  
**Projected size after all phases**: ~10,000-12,000 lines

---

## Extraction Pattern

For each extraction, follow this pattern:

1. **Read** the target functions in `topology.js`
2. **Create** new module file with `window.ModuleName` object
3. **Update** functions to accept `editor` as first parameter
4. **Replace** original functions with delegation wrappers
5. **Update** `index.html` to load new module before `topology.js`
6. **Update** `topology-registry.js` with new module info
7. **Test** functionality works correctly

### Example Wrapper Pattern:
```javascript
// In topology.js
showContextMenu(x, y, obj) {
    if (window.ContextMenus) {
        return window.ContextMenus.showContextMenu(this, x, y, obj);
    }
}
```

### Example Module Pattern:
```javascript
// In topology-context-menus.js
window.ContextMenus = {
    showContextMenu(editor, x, y, obj) {
        // Implementation moved here
        // Replace this.xxx with editor.xxx
    }
};
```

---

## Success Criteria

- [ ] `topology.js` < 10,000 lines
- [ ] No regressions in functionality
- [ ] All modules load without errors
- [ ] Application is crash-immune (errors don't break entire app)
- [ ] Easy to locate and modify features
- [ ] Clear separation of concerns

---

## Notes

- Always test after each extraction
- Keep delegation wrappers for backward compatibility
- Document new modules in `topology-registry.js`
- Follow existing patterns in extracted modules
