# Deployment Guide - December 4, 2025

## 📦 Files Modified Today

### ✅ Files to Upload to Server

**CRITICAL**: Replace these 2 files on your server with the updated versions:

1. **`index.html`** (740 lines)
   - **Changes**: Added VLAN manipulation columns to link table header
   - **Lines Modified**: 679-700
   - **Status**: ✅ Ready to deploy

2. **`topology.js`** (13,728 lines)
   - **Changes**: 
     - Added VLAN manipulation dropdowns and logic
     - Added smart VLAN calculation functions
     - Added text rotation arc meter
     - Added +/- degree format
     - Added adaptive dot sizing
   - **Lines Modified**: ~250 lines across multiple sections
   - **Status**: ✅ Ready to deploy

---

## 🚀 Deployment Instructions

### Option 1: Manual Upload (Recommended)

1. **Backup Current Files** (IMPORTANT!)
   ```bash
   # On your server, backup current files first:
   cp index.html index.html.backup_before_dec4
   cp topology.js topology.js.backup_before_dec4
   ```

2. **Upload New Files**
   ```bash
   # Using SCP (replace with your server details):
   scp index.html user@yourserver.com:/path/to/web/directory/
   scp topology.js user@yourserver.com:/path/to/web/directory/
   ```

3. **Or Using FTP/SFTP Client** (FileZilla, Cyberduck, etc.):
   - Connect to your server
   - Navigate to web directory
   - Upload `index.html` (overwrite)
   - Upload `topology.js` (overwrite)

4. **Verify Deployment**
   - Open your application in browser
   - Hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
   - Test new features

---

### Option 2: Using Git (If you have Git setup)

```bash
# Add the changed files
git add index.html topology.js

# Commit with descriptive message
git commit -m "feat: Add VLAN manipulation and text rotation enhancements

- Added DNOS VLAN manipulation dropdowns (pop, swap, push, etc.)
- Implemented bidirectional VLAN calculation
- Added text rotation arc meter with +/- degree format
- Added adaptive resize/rotate dots for text
- All features tested and linter-clean"

# Push to your repository
git push origin main

# On your server, pull the changes
ssh user@yourserver.com
cd /path/to/web/directory
git pull origin main
```

---

## 📋 Pre-Deployment Checklist

- [ ] Backup current `index.html` on server
- [ ] Backup current `topology.js` on server
- [ ] Clear browser cache before testing
- [ ] Test in production environment
- [ ] Verify all features work correctly

---

## 🔍 What Changed - Detailed Breakdown

### index.html Changes

**Location**: Lines 679-700 (table header)

**Before**:
```html
<th>Device</th>
<th>Interface</th>
<th>VLAN ID</th>
<th>Transceiver</th>
<th>↔</th>
<th>Transceiver</th>
<th>VLAN ID</th>
<th>Interface</th>
<th>Device</th>
```

**After**:
```html
<th>Device</th>
<th>Interface</th>
<th>VLAN Stack</th>
<th>Transceiver</th>
<th>VLAN Manipulation</th>
<th>DNaaS VLAN (Ingress)</th>
<th>↔</th>
<th>DNaaS VLAN (Egress)</th>
<th>VLAN Manipulation</th>
<th>Transceiver</th>
<th>VLAN Stack</th>
<th>Interface</th>
<th>Device</th>
```

**Added**: 4 new columns with gradient styling

---

### topology.js Changes

#### 1. New Properties Initialization (Line 9006-9014)
```javascript
if (!link.device1VlanManipulation) link.device1VlanManipulation = '';
if (!link.device1ManipValue) link.device1ManipValue = '';
if (!link.device2VlanManipulation) link.device2VlanManipulation = '';
if (!link.device2ManipValue) link.device2ManipValue = '';
```

#### 2. Table Body Generation (Lines 9094-9196)
- Added VLAN manipulation dropdowns with DNOS operations
- Added value input fields
- Added auto-calculated DNaaS VLAN fields (read-only, orange background)

#### 3. New Functions Added

**`applyVlanManipulation()` (Lines 9364-9465)**
- Core VLAN transformation logic
- Supports 11 DNOS operations
- Returns formatted VLAN string

**`setupVlanCalculationListeners()` (Lines 9467-9482)**
- Attaches event listeners to all VLAN fields
- Triggers real-time calculation

**`updateDnaasVlanFields()` (Lines 9484-9527)**
- Calculates DNaaS Ingress from Device 1
- Calculates Device 2 Egress from DNaaS Ingress
- Updates read-only fields automatically

#### 4. Save Function Update (Lines 9331-9363)
- Added saving of VLAN manipulation fields
- Stores D1/D2 manipulation type and value

#### 5. Text Rotation Enhancements

**Adaptive Dot Sizing (Lines 12997-12999)**
```javascript
const textDiagonal = Math.sqrt(w * w + h * h);
const dotSize = Math.max(8, Math.min(15, textDiagonal / 15));
```

**Arc Meter Rendering (Lines 13011-13026)**
```javascript
// Draw background circle
this.ctx.arc(corner.x, corner.y, arcRadius, 0, Math.PI * 2);
// Draw green arc from 0° to current rotation
this.ctx.arc(corner.x, corner.y, arcRadius, 0, rotationRadians);
```

**+/- Degree Format (Lines 13053-13057, 13091, 10755-10761)**
```javascript
let degrees = Math.round(text.rotation || 0) % 360;
if (degrees > 180) degrees -= 360;
if (degrees < -180) degrees += 360;
const labelText = degrees >= 0 ? `+${degrees}°` : `${degrees}°`;
```

---

## 🧪 Post-Deployment Testing

### Test 1: VLAN Manipulation
```
1. Create link between two devices
2. Double-click link
3. Enter D1 VLAN: 100.200
4. Select D1 Manipulation: pop-pop
5. ✅ Verify: DNaaS Ingress shows "(empty)"
6. Select D2 Manipulation: push, Value: 300
7. ✅ Verify: D2 Egress shows "300"
```

### Test 2: Text Rotation
```
1. Press T, place text
2. Select text
3. Grab green rotation dot
4. ✅ Verify: Green arc meter appears
5. ✅ Verify: Angle shows "+45°" format
6. ✅ Verify: Dots scale with text size
```

### Test 3: Backward Compatibility
```
1. Load existing topology (if you have one saved)
2. ✅ Verify: All objects load correctly
3. ✅ Verify: No console errors
4. ✅ Verify: Old links work without VLAN data
```

---

## 🔧 Troubleshooting

### Issue: Features Don't Appear

**Solution**: Hard refresh browser
```
Mac: Cmd + Shift + R
Windows/Linux: Ctrl + Shift + R
```

### Issue: Console Errors

**Check**: Files uploaded completely
```bash
# On server, verify file sizes:
ls -lh index.html topology.js

# index.html should be ~30-35 KB
# topology.js should be ~680-690 KB
```

### Issue: Old Version Still Showing

**Solution**: Clear browser cache or version the files
```html
<!-- In index.html, add version parameter: -->
<script src="topology.js?v=20251204"></script>
```

---

## 📊 Server Requirements

### No New Requirements
✅ No new dependencies needed  
✅ No server-side changes required  
✅ Pure client-side JavaScript enhancements  
✅ Works with existing setup

---

## 🔄 Rollback Instructions

If you need to revert to the previous version:

```bash
# On server, restore backups:
cp index.html.backup_before_dec4 index.html
cp topology.js.backup_before_dec4 topology.js
```

Or using Git:
```bash
git revert HEAD
git push origin main
```

---

## 📞 Deployment Checklist for Server Admin

Dear Server Admin,

Please replace these files on the production server:

**Files to Replace**:
1. ✅ `index.html` - Link table header updated
2. ✅ `topology.js` - VLAN logic and text rotation features added

**Backup First** (IMPORTANT):
- Save current `index.html` as `index.html.backup_before_dec4`
- Save current `topology.js` as `topology.js.backup_before_dec4`

**Deployment Steps**:
1. Create backups of current files
2. Upload/copy new `index.html` (overwrite existing)
3. Upload/copy new `topology.js` (overwrite existing)
4. Clear server cache if applicable
5. Test application after deployment

**New Features Added**:
- DNOS VLAN manipulation with real-time calculation
- Text rotation arc meter with +/- degree format
- Adaptive resize/rotate dots for text

**Compatibility**: 
- ✅ No breaking changes
- ✅ Backward compatible with existing data
- ✅ No new dependencies
- ✅ Pure client-side enhancements

**Testing**:
After deployment, verify:
- Link table opens correctly
- New VLAN columns appear
- Text rotation shows arc meter
- No console errors

Thank you!

---

## 📅 Deployment Information

**Date**: December 4, 2025  
**Version**: 1.1.0 (VLAN + Text Enhancements)  
**Files Modified**: 2 (`index.html`, `topology.js`)  
**Lines Added**: ~250 lines  
**Breaking Changes**: None  
**Dependencies**: None  

---

## ✅ Deployment Status

- [ ] Files backed up on server
- [ ] `index.html` uploaded to server
- [ ] `topology.js` uploaded to server
- [ ] Browser cache cleared
- [ ] VLAN manipulation tested
- [ ] Text rotation tested
- [ ] Production verified

**Deployed by**: _____________  
**Deployment Date**: _____________  
**Deployment Time**: _____________  

---

## 📞 Support

If you encounter any issues during deployment:
1. Check file sizes match expected values
2. Verify no upload errors occurred
3. Clear browser cache completely
4. Check browser console for errors
5. Restore from backup if needed

**Files Ready for Deployment** ✅


