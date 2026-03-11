# Browser MCP Server Setup

## Issue Found
The browser MCP server (`cursor-ide-browser`) is showing "No server info found" errors in the logs, preventing browser automation tools from working.

## Root Cause
The browser automation extension is a built-in Cursor extension that should activate automatically on startup, but it's failing to register properly with the MCP system.

## Current Status
- ✅ Browser extension files exist: `cursor-browser-automation` and `cursor-browser-extension`
- ✅ Extension is configured to activate on `onStartupFinished`
- ❌ Server is not initializing properly (showing "No server info found" errors)
- ❌ Browser tools are available but return "No server found" when called

## Logs Location
Browser server logs are located at:
- `~/.cursor-server/data/logs/[DATE]/exthost*/anysphere.cursor-mcp/MCP cursor-ide-browser.log`
- `~/.cursor-server/data/logs/[DATE]/exthost*/anysphere.cursor-mcp/MCP cursor-browser-extension.log`

## Solutions to Try

### 1. Restart Cursor IDE
The browser extension activates on startup. A full restart may fix initialization issues:
```bash
# Close Cursor completely and reopen
```

### 2. Check Cursor Settings
The browser automation may need to be enabled in Cursor settings:
- Open Cursor Settings (Ctrl+, or Cmd+,)
- Search for "browser" or "automation"
- Ensure browser automation features are enabled

### 3. Check Extension Status
Verify the browser extension is enabled:
- Open Extensions view (Ctrl+Shift+X)
- Search for "Cursor Browser Automation"
- Ensure it's enabled

### 4. Clear Extension Cache
If the extension is corrupted:
```bash
# Backup and clear extension cache
mv ~/.cursor-server/data/logs ~/.cursor-server/data/logs.backup
# Restart Cursor
```

### 5. Reinstall Cursor (Last Resort)
If nothing else works, reinstalling Cursor may fix extension initialization issues.

## Note
The JavaScript fixes made to `topology.js` should resolve the white screen issue regardless of browser tool availability. You can test the application at `http://localhost:8080` using your regular browser.

## Browser Tools Available (When Working)
- `mcp_cursor-ide-browser_browser_navigate` - Navigate to URL
- `mcp_cursor-ide-browser_browser_snapshot` - Capture page snapshot
- `mcp_cursor-ide-browser_browser_click` - Click elements
- `mcp_cursor-ide-browser_browser_type` - Type text
- And more...

These tools require the browser MCP server to be properly initialized.


