# Enhanced Recovery Detection - Complete Implementation

## Summary

Enhanced SCALER to detect and display **specific recovery modes** instead of generic "RECOVERY", and added **console access guidance** for PE-2 when SSH is unavailable.

---

## Changes Made

### 1. Enhanced Recovery Type Detection

**Monitor (`monitor.py`):**
- Updated `_detect_recovery_from_config()` to return tuple: `(in_recovery: bool, recovery_type: str)`
- Detects 3 specific recovery types:
  - **DN_RECOVERY** - All NCCs down (NCC: 0/X UP) or no uptime + all interfaces down
  - **STANDALONE** - One NCC down (NCC: 1/2 UP) - degraded but operational
  - **GI** - Device in Golden Image mode (future detection)

**Detection Logic:**
```python
if ncc_up == 0 and ncc_total > 0:
    return True, "DN_RECOVERY"  # Critical boot failure
elif ncc_up == 1 and ncc_total == 2:
    return True, "STANDALONE"   # Degraded redundancy
```

### 2. Operational.json Schema Enhancement

**New field added:**
```json
{
  "recovery_mode_detected": true,
  "recovery_type": "DN_RECOVERY",  // NEW: DN_RECOVERY | STANDALONE | GI | ""
  "recovery_mode_detected_at": "2026-01-27T17:39:41.719725"
}
```

### 3. Monitor Display Enhancement

**Before:**
```
PE-2  SA-36CD-S  N/A  4m ago  ⚠ RECOVERY
```

**After:**
```
PE-2  SA-36CD-S  N/A  4m ago  ⚠ DN_RECOVERY
```

**Color coding:**
- 🔴 **DN_RECOVERY** - Bold red (critical)
- 🟡 **STANDALONE** - Yellow (warning)
- 🟡 **GI_MODE** - Yellow (waiting for deployment)

### 4. Wizard Display Enhancement

**Device table now shows specific recovery type:**
```
╭───┬─────┬──────────┬───────────┬──────────────────┬──────────────╮
│ # │ ID  │ Hostname │ Type      │ Last Sync        │ Status       │
├───┼─────┼──────────┬───────────┼──────────────────┼──────────────┤
│ 2 │ pe2 │ PE-2     │ SA-36CD-S │ 2026-01-27 17:39 │ DN_RECOVERY  │
╰───┴─────┴──────────┴───────────┴──────────────────┴──────────────╯
```

### 5. Console Access Guidance (PE-2)

**When selecting PE-2 in recovery mode:**
```
⚠ PE-2 is in DN_RECOVERY mode

📡 Console Access Required for PE-2:
  SSH access unavailable (mgmt0 IP deleted in recovery)
  Connect via console server:
    ssh dn@console-b15
    Select: [3] Port access
    Port: [13] PE-2
    Login: dnroot / dnroot

  Recommended Action: Use [S] System Restore wizard

Continue with this device? [Y/n]:
```

**Why PE-2 needs console:**
- After recovery mode, **mgmt0 IP gets deleted**
- Not in DNS, only IP access normally
- Console is the ONLY way to access PE-2 in recovery

---

## Recovery Type Definitions

### DN_RECOVERY (Critical 🔴)
**Indicators:**
- All NCCs down: `NCC: 0/1 UP` or `NCC: 0/2 UP`
- No uptime: `Uptime: N/A`
- All interfaces down: `Total: X configured / 0 UP`

**What it means:**
- Device failed to boot DNOS properly
- Stuck in emergency boot environment
- No data plane, minimal control plane
- CLI accessible but limited functionality

**Recovery:**
- Use **System Restore wizard** `[S]`
- Or manual: `request system restore factory-default`
- Then reload images and deploy DNOS

---

### STANDALONE (Warning 🟡)
**Indicators:**
- One NCC down: `NCC: 1/2 UP (Standalone)`
- System otherwise functional

**What it means:**
- Lost NCC redundancy
- Single point of failure (one more NCC failure = full outage)
- Control plane running on surviving NCC
- Data plane may be partially affected

**Recovery:**
- Check logs for NCC failure reason
- Try: `request system ncc reload ncc-id X`
- If hardware failure: RMA required
- System continues operating (schedule maintenance)

---

### GI_MODE (Warning 🟡)
**Indicators:**
- Prompt shows: `GI(system-type)#` or `GI>`
- DNOS not deployed

**What it means:**
- Container orchestration layer running
- Waiting for DNOS deployment
- Clean state after factory reset
- Or DNOS failed to deploy

**Recovery:**
- Load images: `request system target-stack load <URL>`
- Deploy DNOS: `request system deploy system-type X name Y ncc-id 0`
- Or use **Image Upgrade wizard** `[6]`

---

## Console Access for PE-2

### When Needed
- Device in DN_RECOVERY mode
- SSH fails (mgmt0 IP deleted)
- Not in DNS (IP-only access)

### Access Steps
```bash
# 1. SSH to console server
ssh dn@console-b15
Password: drive1234

# 2. Select port access
Select: 3

# 3. Select PE-2 port
Port: 13

# 4. Login to device
Login: dnroot
Password: dnroot

# 5. Now at PE-2 console
dnRouter(RECOVERY)#
```

### Console Features
- **Direct serial access** - bypasses network issues
- **See boot messages** - kernel panics, errors
- **Access in all modes** - RECOVERY, GI, DNOS
- **Out-of-band** - works even if management network down

---

## Testing

**Verify recovery type detection:**
```bash
# Run monitor
cd /home/dn/SCALER
python3 monitor.py --once

# Expected output:
PE-2  SA-36CD-S  N/A  ⚠ DN_RECOVERY
```

**Verify wizard display:**
```bash
scaler-wizard

# Select device, should show:
│ 2 │ pe2 │ PE-2 │ SA-36CD-S │ ... │ DN_RECOVERY │

# When selecting PE-2:
⚠ PE-2 is in DN_RECOVERY mode
📡 Console Access Required for PE-2:
...
```

**Check operational.json:**
```bash
jq '.recovery_mode_detected, .recovery_type' db/configs/PE-2/operational.json
# Output:
true
DN_RECOVERY
```

---

## Files Modified

1. **`monitor.py`:**
   - Enhanced `_detect_recovery_from_config()` - returns recovery type
   - Updated `_persist_recovery_status()` - stores recovery_type
   - Modified `scan_devices()` - tracks recovery_type
   - Enhanced status display - shows specific type

2. **`scaler/interactive_scale.py`:**
   - Updated `select_device()` - shows specific recovery type
   - Added console access guidance for PE-2
   - Enhanced device table - displays DN_RECOVERY/STANDALONE/GI_MODE

3. **`docs/RECOVERY_ENHANCEMENT.md`:**
   - NEW: This documentation file

---

## User Experience Flow

**Scenario: PE-2 in Recovery**

1. **User runs monitor:**
   ```
   PE-2  SA-36CD-S  N/A  ⚠ DN_RECOVERY  ← Specific type shown
   
   ⚠ RECOVERY MODE DETECTED - 1 device(s)
     • PE-2 (SA-36CD-S)
   ```

2. **User opens wizard:**
   ```
   │ 2 │ pe2 │ PE-2 │ SA-36CD-S │ ... │ DN_RECOVERY │  ← Type visible
   ```

3. **User selects PE-2:**
   ```
   ⚠ PE-2 is in DN_RECOVERY mode
   
   📡 Console Access Required for PE-2:  ← Guidance shown
     ssh dn@console-b15
     ...
     Recommended Action: Use [S] System Restore wizard
   
   Continue with this device? [Y/n]:
   ```

4. **User knows:**
   - Exact recovery type (DN_RECOVERY = boot failure)
   - How to access (console commands provided)
   - What to do ([S] System Restore)

---

## Benefits

### 1. Better Diagnostics
- **Before:** "RECOVERY" - unclear what kind
- **After:** "DN_RECOVERY" - boot failure, need factory reset

### 2. Actionable Guidance
- **Before:** User confused how to access PE-2
- **After:** Console commands provided, clear steps

### 3. Reduced Escalations
- User can self-serve with clear instructions
- No need to ask "how do I access PE-2?"

### 4. Future Extensibility
- Easy to add more recovery types (e.g., GI detection from prompt)
- Console guidance pattern reusable for other devices

---

**Status:** ✅ Complete and Tested  
**Date:** 2026-01-27  
**Impact:** Users can now see specific recovery types and know exactly how to access devices in recovery mode, especially PE-2 via console.
