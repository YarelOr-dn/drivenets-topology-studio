# Verification Steps for Recent Changes

## Changes Made:

### 1. Font Controls in Device Rename Popup
- **Location**: `showRenamePopup()` function (line ~30293)
- **Status**: Code is correct - font controls are created before being referenced
- **To Verify**: 
  - Right-click a device → "Change Label"
  - Should see "Font Settings" section with Family, Size, Weight, Style dropdowns

### 2. Detach Link from Device
- **Location**: Context menu (line ~27138) and handler (line ~30998)
- **Status**: Code is correct
- **To Verify**:
  - Right-click a link that's attached to a device
  - Should see "Detach from Device" option in context menu

### 3. Duplicate TB with Attached Link
- **Location**: `duplicateObject()` function (line ~18750)
- **Status**: Code checks for `obj.linkId` and duplicates link if found
- **To Verify**:
  - Select a text box attached to a link
  - Right-click → "Duplicate"
  - Should duplicate both the link AND the text box

### 4. UL Deletion Aborts QUL Creation
- **Location**: `deleteSelected()` function (line ~32163)
- **Status**: Code checks `_linkFromTP` and aborts if source UL is being deleted
- **To Verify**:
  - Click on a UL TP to start QUL creation (orange line should appear)
  - Delete the source UL (the one you clicked the TP on)
  - QUL mode should abort, orange line should disappear, mode should be base

## Debugging Steps:

1. **Hard Refresh Browser**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Check Browser Console**: Open DevTools (F12) → Console tab, look for JavaScript errors
3. **Check if file is loading**: In DevTools → Network tab, verify `topology.js` is loading (not cached)
4. **Add cache-busting**: If using a web server, add `?v=timestamp` to the script tag in HTML

## Common Issues:

- **Browser Cache**: Old JavaScript file is cached - hard refresh required
- **File Not Saved**: Make sure topology.js was saved
- **JavaScript Errors**: Check browser console for runtime errors
- **Wrong File**: Verify you're editing the correct topology.js file
