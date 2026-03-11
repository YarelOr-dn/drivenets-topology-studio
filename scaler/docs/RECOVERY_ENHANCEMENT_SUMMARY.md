# Recovery System Enhancement Summary

## What Was Implemented

### 1. **State-Specific Detection & Display**

**Monitor (`monitor.py`):**
- ✅ Detects exact device state: ONIE, BASEOS_SHELL, DN_RECOVERY, GI, STANDALONE
- ✅ Updates `operational.json` with live-detected state
- ✅ Shows specific status in device table (not generic "RECOVERY")
- ✅ Provides detailed state summary with cause and fix

**Wizard (`interactive_scale.py`):**
- ✅ Header shows specific state: `PE-2 BASEOS_SHELL` (not `PE-2 RECOVERY`)
- ✅ Device table shows specific state in Status column
- ✅ Status matches monitor exactly (same colors, same labels)

---

### 2. **State-Specific Recovery Workflows**

#### **ONIE Mode**
```
[1] Launch System Restore
    ↓ Install BaseOS
    ↓ Reboot into BaseOS Shell
    ↓ Run dncli → GI mode
    ↓ ✓ System Restore completed
    ↓ "Continue to Image Upgrade?" [Y/n]
    ↓ Load images + Deploy DNOS
    ↓ ✓ Device fully operational

[2] Manual recovery instructions (ONIE commands)
[3] Continue to main menu
[B] Back to device selection
```

#### **BASEOS_SHELL Mode**
```
[1] Launch System Restore
    ↓ Login with dn/drivenets
    ↓ Run dncli → GI mode
    ↓ ✓ System Restore completed - Device is now in GI mode
    ↓ "Continue to Image Upgrade?" [Y/n]
    ↓ Load images + Deploy DNOS
    ↓ ✓ Device fully operational

[2] Manual recovery instructions (dncli commands)
[3] Continue to main menu
[B] Back to device selection
```

#### **DN_RECOVERY Mode**
```
[1] Launch System Restore
    ↓ Factory reset to GI mode
    ↓ ✓ System Restore completed - Device is now in GI mode
    ↓ "Continue to Image Upgrade?" [Y/n]
    ↓ Load images + Deploy DNOS
    ↓ ✓ Device fully operational

[2] Manual recovery instructions (factory-default commands)
[3] Continue to main menu
[B] Back to device selection
```

#### **GI Mode**
```
[1] Launch Image Upgrade wizard (recommended)
    ↓ Select Jenkins build or manual images
    ↓ Load DNOS/GI/BaseOS images
    ↓ Deploy DNOS
    ↓ ✓ Device fully operational

[2] Continue to main menu
[B] Back to device selection
```

#### **STANDALONE Mode**
```
[1] View diagnostic commands
    • show system
    • show ncc status
    • show logging | match NCC
    • show system stack

[2] Continue to main menu
[B] Back to device selection

Note: Requires manual investigation (hardware/software issue)
```

---

### 3. **Automatic Workflow Continuity**

**Key Feature:** After System Restore completes successfully, the wizard **automatically offers** to continue with Image Upgrade.

**Flow:**
1. System Restore brings device to GI mode
2. Wizard prompts: "Continue to Image Upgrade to load images and deploy DNOS? [Y/n]"
3. If user confirms [Y], Image Upgrade wizard launches immediately
4. User selects images and deploys
5. Device becomes fully operational

**Benefits:**
- No need to remember to run Image Upgrade separately
- Single continuous flow from recovery to deployment
- Reduces manual steps and potential errors
- User can still decline and do it manually later

---

### 4. **Manual Recovery Options**

Every state now offers **[2] Manual recovery instructions**:

**ONIE:**
- EEPROM check
- Partition management
- BaseOS installation commands

**BASEOS_SHELL:**
- Login credentials
- dncli command
- GI mode verification

**DN_RECOVERY:**
- Factory reset command
- Mgmt IP configuration
- Image Upgrade guidance

**STANDALONE:**
- Diagnostic commands
- Investigation steps
- Hardware/software checks

---

## Files Modified

1. **`/home/dn/SCALER/monitor.py`**
   - Added `update_device_state_live()` function
   - Enhanced `get_device_status()` to load recovery fields
   - Multi-path connection strategy integration
   - State-specific display in device table
   - Comprehensive detection summary

2. **`/home/dn/SCALER/scaler/interactive_scale.py`**
   - Enhanced `_print_db_status_header()` for specific recovery types
   - Enhanced device table status column (lines 12307-12335)
   - Added ONIE recovery workflow (lines 12500-12565)
   - Enhanced BASEOS_SHELL workflow with continuity (lines 12570-12630)
   - Enhanced DN_RECOVERY workflow with continuity (lines 12635-12695)
   - Added STANDALONE diagnostic workflow (lines 12700-12740)
   - GI mode already had Image Upgrade launch capability

3. **`/home/dn/SCALER/docs/RECOVERY_WORKFLOW_COMPLETE.md`** (NEW)
   - Complete documentation of all recovery workflows
   - State-specific guidance
   - Automated vs manual paths
   - Example end-to-end recovery

---

## Testing Checklist

### For BASEOS_SHELL State (Current PE-2 state):

1. **Restart wizard** to load new code:
   ```bash
   # Exit current wizard (Ctrl+C or [B])
   scaler-wizard
   ```

2. **Verify status display:**
   - Header should show: `PE-2 BASEOS_SHELL` (not `PE-2 RECOVERY`)
   - Table should show: `│ ... │ BASEOS_SHELL │`

3. **Select PE-2:**
   - Panel should show: "⚠ BASEOS SHELL"
   - Cause: "GI container not running"
   - Recovery path shown clearly

4. **Launch System Restore:**
   - Select [1] Launch System Restore
   - Wizard should detect BaseOS Shell
   - Should run dncli → GI mode
   - After success: "Continue to Image Upgrade?" prompt

5. **Test continuity:**
   - Confirm [Y] to continue
   - Image Upgrade wizard should launch
   - Select build and deploy
   - Device should reach DNOS operational state

### For Other States:

- **GI Mode:** Should directly offer Image Upgrade
- **DN_RECOVERY:** Should offer factory reset → GI → Image Upgrade
- **ONIE:** Should offer BaseOS install → dncli → GI → Image Upgrade
- **STANDALONE:** Should offer diagnostic commands (no auto-fix)

---

## User Experience Improvements

### Before:
```
Status: RECOVERY (generic, unclear what's wrong)
Action: System Restore (but then what?)
Result: Device in GI mode (now what? User must remember Image Upgrade)
```

### After:
```
Status: BASEOS_SHELL (specific, clear state)
Action: Launch System Restore (dncli → GI → images → deploy)
Result: System Restore → Auto-prompt for Image Upgrade → Complete deployment
```

**Key Improvements:**
1. ✅ **Clarity:** Exact state shown everywhere
2. ✅ **Guidance:** State-specific recovery paths
3. ✅ **Automation:** Continuous flow from recovery to deployment
4. ✅ **Flexibility:** Manual options always available
5. ✅ **Consistency:** Monitor and wizard show same status

---

## Next Steps

1. **Test with PE-2** (currently in BASEOS_SHELL)
2. **Test ONIE mode** when available
3. **Test DN_RECOVERY** when needed
4. **Verify Image Upgrade integration** works correctly
5. **Document any edge cases** discovered during testing

---

## Documentation

Complete documentation created:

1. **`RECOVERY_WORKFLOW_COMPLETE.md`** - Full workflow guide
2. **`STATE_DETECTION_MITIGATION_GUIDE.md`** - Detection matrix
3. **`AUTOMATIC_MITIGATION_PROMPTS.md`** - Prompt reference
4. **`AUTOMATIC_MITIGATION_FLOWCHART.md`** - Visual guide

All documentation includes:
- State-specific guidance
- Automated vs manual paths
- Console access info
- Credential reference
- Example flows
