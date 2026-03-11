# 🐛 Debugger Integration Guide

## Overview
The visual debugger automatically tracks all operations in the Topology Editor. It's designed to work with **all future features** without manual integration.

## How to Use

### Opening/Closing
- **Press `D`** (when not typing in an input) → Toggle debugger
- **Press `Shift+D`** → Global toggle (works anywhere)
- **Click `✕` button** → Close debugger
- **Click `_` button** → Minimize/maximize
- **Click `Clear` button** → Clear event log

### Features
- **Draggable** — Click and drag the header to move anywhere
- **Persistent** — Remembers position, minimized state, and visibility
- **Auto-updates** — Refreshes every 100ms

## Integrating with New Features

### Quick Integration (Recommended)
Add logging to any operation using these simple methods:

```javascript
// Success message (green ✅)
if (this.debugger) {
    this.debugger.logSuccess('Device rotated 90°');
}

// Action message (purple 🔹)
if (this.debugger) {
    this.debugger.logAction('Creating new link');
}

// Warning message (yellow ⚠️)
if (this.debugger) {
    this.debugger.logWarning('Device name already exists');
}

// Error message (red ❌)
if (this.debugger) {
    this.debugger.logError('Failed to save topology');
}

// Info message (cyan ℹ️)
if (this.debugger) {
    this.debugger.logInfo('Loading from localStorage');
}
```

### Advanced Integration

**State Changes:**
```javascript
// Track property changes
if (this.debugger) {
    this.debugger.logStateChange('Zoom', '100%', '150%');
}
```

**Object Operations:**
```javascript
// Track object operations
if (this.debugger) {
    this.debugger.logObjectOperation('add', 'device', 1);      // ➕ add 1 device
    this.debugger.logObjectOperation('delete', 'link', 3);    // 🗑️ delete 3 links
    this.debugger.logObjectOperation('move', 'device', 5);    // ↔️ move 5 devices
    this.debugger.logObjectOperation('resize', 'device', 1);  // 📐 resize 1 device
    this.debugger.logObjectOperation('rotate', 'device', 1);  // 🔄 rotate 1 device
}
```

## Auto-Logging Features

The debugger **automatically** captures:
- ✅ All `console.log()` calls with "saveState" → "💾 State saved"
- ✅ All `console.log()` calls with "undo/redo" → Action logged
- ✅ All `console.error()` calls → Red error messages
- ✅ All `console.warn()` calls → Yellow warnings
- ✅ Modal open/close operations
- ✅ Mode transitions

## What the Debugger Shows

### 📊 History State
- Current history index (which step you're on)
- Total history length (how many steps exist)
- Can Undo / Can Redo status (green YES / red NO)

### 🎯 Current State
- Object counts (devices, links, text)
- Selected objects count
- MultiSelect mode status
- Dragging/Placing status
- Current mode

### 📜 Event Log
- Last 30 events with timestamps
- Color-coded by type
- Auto-scrolls to latest

## Template for New Features

When adding a new feature, follow this template:

```javascript
myNewFeature() {
    // 1. Log the action start
    if (this.debugger) {
        this.debugger.logAction('New feature started');
    }
    
    // 2. Save state if modifying objects
    this.saveState();
    
    // 3. Perform the operation
    // ... your code here ...
    
    // 4. Log success or error
    try {
        // ... operation ...
        if (this.debugger) {
            this.debugger.logSuccess('Feature completed successfully');
        }
    } catch (error) {
        if (this.debugger) {
            this.debugger.logError('Feature failed: ' + error.message);
        }
    }
    
    // 5. Update UI and auto-save
    this.draw();
    this.scheduleAutoSave();
}
```

## Console Commands

Use these in the browser console (F12):

```javascript
// Check auto-save state
window.checkAutoSave()

// Check history state
window.checkHistory()

// Show debugger
window.debugger.show()

// Hide debugger
window.debugger.hide()

// Toggle debugger
window.debugger.toggle()

// Clear log
window.debugger.logs = []
window.debugger.updateLogDisplay()
```

## Troubleshooting

**Debugger not visible?**
- Press `D` or `Shift+D` to toggle
- Check localStorage: `localStorage.getItem('debugger_enabled')`
- Force show: `window.debugger.show()`

**Not logging events?**
- Check if `this.debugger` exists
- Check browser console for errors
- Verify debugger.js is loaded before topology.js

**Lost the debugger window?**
- Reset position: `localStorage.removeItem('debugger_position')`
- Refresh page

## Design
- Matrix-style green terminal aesthetic
- Semi-transparent black background
- Color-coded messages
- Minimal, non-intrusive
- Stays on top of all elements

