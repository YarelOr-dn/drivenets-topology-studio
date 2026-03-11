# 📝 Network Topology Creator - App Changelog

## ⚠️ AGENT INSTRUCTIONS
**ALL agents working on this app MUST:**
1. Update this changelog after making ANY changes
2. Test changes before committing
3. Document new features, bug fixes, and breaking changes
4. Include the date and brief description

---

## Changelog

### 2026-01-08 - DriveNets Blue Primary Color Update
**Status:** ✅ APPLIED

#### Updated Brand Colors (Matches Documentation Portal)
- **Top Bar**: Now uses DriveNets Blue gradient (#1976D2 → #1565C0)
- **All UI Elements**: Transitioned from cyan to blue accent colors
- **Moving Points (MP)**: Blue (#1976D2 normal, #42A5F5 selected)
- **Borders & Highlights**: Blue (#1976D2) instead of cyan
- **CSS Variables**: Added full DriveNets brand color system

#### New CSS Variables (`:root`)
```css
--dn-blue: #1976D2       /* Primary DriveNets Blue */
--dn-blue-light: #2196F3  /* Hover states */
--dn-blue-dark: #0D47A1   /* Active/pressed states */
--dn-cyan: #00B4D8        /* Legacy accent (still available) */
--dn-orange: #E67E22      /* Call to action */
--dn-navy: #0D1B2A        /* Dark backgrounds */
--dn-navy-light: #1B263B  /* Secondary backgrounds */
```

#### Files Modified
- `topology.js` - Updated 10 color references
- `index.html` - Updated BD badge, stroke button, default colors
- `styles.css` - Added CSS variables, updated accent colors throughout

---

### 2026-01-07 - DriveNets Brand Design + Device Fonts + CP Fixes
**Status:** ✅ APPLIED

#### DriveNets Brand Design (MAJOR UPDATE)
- **Top Bar**: Dark navy gradient (#1B263B → #0D1B2A) with cyan accents
- **Left Toolbar**: Dark navy background with cyan borders and highlights
- **Buttons**: Cyan (#00B4D8) hover effects with glow
- **Section Headers**: Cyan uppercase text with letter spacing
- **Overall**: Professional, modern DriveNets corporate style

#### Brand Colors Used
- Primary Navy: `#0D1B2A`
- Secondary Navy: `#1B263B`  
- Accent Cyan: `#00B4D8`
- Accent Orange: `#E67E22`
- Light Text: `#E0E6ED`

#### Control Points (CP) - FIXED
- Color changed from purple to **orange** (#E67E22, #F39C12, #D35400)
- Handle size increased (8px normal, 10px active)
- Better visibility and hover feedback
- Orange glow effect on hover

### 2026-01-07 - Device Font System & CP Fixes
**Status:** ✅ APPLIED to topology.js

#### Device Label Fonts Feature
- Added `defaultDeviceFontFamily` property in constructor (line ~412)
- Font options: Inter, DM Sans, Space Grotesk, JetBrains Mono, Fira Code, Caveat
- UI grid in index.html: `#device-font-grid` with `.font-btn` buttons
- Applies to selected devices AND sets default for new devices
- Saved to localStorage: `defaultDeviceFontFamily`

#### Text Box (TB) Fonts
- Font Family selector in Text options toolbar
- Options: Sans (Inter), Brand (IBM Plex Sans), Hand (Caveat), Mono (IBM Plex Mono), Serif (Georgia), Sketch (Comic Neue)
- Applied via `data-font` attribute on buttons

#### Orange Connection Points (CP)
- Manual curve control points use orange (#E67E22) theme color
- CP handle appears when hovering over links with manual curve mode
- CP can be dragged to adjust curve shape
- Fixed: CP handle position matches actual curve t=0.5 point

#### Files Modified
- `topology.js` - Main logic for fonts and CP handling
- `index.html` - UI elements for font selection
- `styles.css` - Styling for font buttons and CP handles

---

### Recent Features (Dec 2025 - Jan 2026)

#### Spherical/Circular Curves
- Manual curve creates spherical arcs instead of parabolic curves
- Near-perfect semicircle approximation
- Commit: `524d860`

#### DNAAS Hierarchical Layout
- Tree layout: SuperSpine → Spine → Leaf → PE
- Commit: `78f8e74`

#### CP Sync with Device Movement
- Manual curve CP syncs when devices move
- Commits: `5156377`, `5a5b4ec`, `ae0e4a9`

#### Link Attachment Toggle
- Global toggle for link attachments in Text options toolbar
- Commit: `c59e453`

---

## 🔧 Known Issues

1. **Console Errors (POST to 127.0.0.1:7242)** - These are Cursor telemetry errors, NOT app bugs
2. **Unsaved Changes** - Device font features may be in editor but not saved to file

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `topology.js` | Main app logic (~30k lines) |
| `index.html` | UI structure and elements |
| `styles.css` | Visual styling |
| `debugger.js` | Debug panel |
| `scaler-gui.js` | SCALER integration UI |

---

## 🎨 Design System

### Colors (Dark Mode Theme)
- Background: `#0D1B2A` (dark navy)
- Primary Accent: `#00B4D8` (cyan)
- Secondary Accent: `#E67E22` (orange)
- Success: `#27ae60` (green)
- Error: `#e74c3c` (red)
- Text: `#ECF0F1` (light gray)

### Fonts
- **Default UI:** Inter, system fonts
- **Device Labels:** Inter, DM Sans, Space Grotesk, JetBrains Mono, Fira Code, Caveat
- **Text Boxes:** Inter, IBM Plex Sans, Caveat, IBM Plex Mono, Georgia, Comic Neue

---

## 📋 Agent Workflow (MANDATORY)

### ⚠️ CRITICAL: All agents MUST follow this workflow

**When making ANY changes to the app:**

### 1. Before Starting
```bash
# Check for uncommitted changes
cd /home/dn/CURSOR && git status --short

# Check current line count
wc -l topology.js index.html styles.css

# Read this changelog
cat APP_CHANGELOG.md | head -100
```

### 2. While Working
- Use `sed` to verify actual saved file content (not just `read_file` which shows editor content)
- Test changes in browser at http://100.64.6.134:8080
- Check browser console (F12) for JavaScript errors
- Verify existing features still work

### 3. After Completing Changes
```bash
# Verify changes are in the saved file
grep -c "YOUR_NEW_FEATURE" topology.js

# Update cache buster in index.html
sed -i 's/topology.js?v=[^"]*"/topology.js?v=YYYYMMDD_feature/' index.html

# Update this changelog
# Add new entry under "## Changelog" section
```

### 4. Update This Changelog
Add a new entry with:
- **Date**: YYYY-MM-DD format
- **Title**: Brief description
- **Status**: ✅ APPLIED, ⏳ PENDING, ❌ REVERTED
- **Details**: What was added/changed/fixed
- **Files Modified**: List of files

### 5. Commit (but DON'T push without user approval)
```bash
git add topology.js index.html styles.css APP_CHANGELOG.md
git commit -m "Brief description of changes"
# Do NOT git push - wait for user approval
```

---

## 🔍 Troubleshooting

### "Features are missing after reload"
- Editor shows unsaved content vs actual file on disk
- Use `sed -n 'LINE1,LINE2p' topology.js` to verify actual file content
- Use `grep -n "feature_name" topology.js` to find if feature exists

### "Console errors (POST to 127.0.0.1:7242)"
- These are Cursor IDE telemetry errors, NOT app bugs
- Ignore them - they don't affect the app

### "App not updating after code changes"
- Update cache buster: `?v=YYYYMMDD` in index.html
- Hard refresh: Ctrl+Shift+R
- Check server is running: `ps aux | grep uvicorn`

---

*Last updated: 2026-01-08*

