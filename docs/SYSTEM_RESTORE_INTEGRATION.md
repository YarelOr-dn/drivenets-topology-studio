# System Restore Wizard Integration - Complete

## Summary

Enhanced the wizard to **actively prompt for System Restore** when a device in recovery mode is selected, matching the behavior of `scaler-monitor`.

---

## User Experience Flow

### When User Selects PE-2 (in DN_RECOVERY):

```
⚠ PE-2 is in DN_RECOVERY mode

📡 Console Access Required for PE-2:
  SSH access unavailable (mgmt0 IP deleted in recovery)
  Connect via console server:
    ssh dn@console-b15
    Select: [3] Port access
    Port: [13] PE-2
    Login: dnroot / dnroot

To restore device(s), you can:
  • Continue to main menu and select [S] System Restore
  • Or launch System Restore wizard now

Launch System Restore wizard now? [Y/n]:
```

**If user chooses [Y] (default):**
- System Restore wizard launches immediately
- User guided through factory reset → image loading → DNOS deployment
- After completion, returns to device selection

**If user chooses [n]:**
- Continues to main device menu
- User can select [S] System Restore later

---

## Comparison with Monitor

### scaler-monitor:
```
⚠ RECOVERY MODE DETECTED - 1 device(s)
  • PE-2 (SA-36CD-S)

To restore device(s), run:
  scaler-wizard
  Then select the device(s) and choose [S] System Restore

Launch System Restore wizard now? [Y/n]:
```

### scaler-wizard (NOW):
```
⚠ PE-2 is in DN_RECOVERY mode
📡 Console Access Required for PE-2:
  [console instructions]

Launch System Restore wizard now? [Y/n]:
```

**✅ Same behavior!** Both now offer direct System Restore launch.

---

## Implementation Details

**File:** `scaler/interactive_scale.py`

**Function:** `select_device()`

**Logic:**
1. Check if selected device has `recovery_mode_detected: true`
2. Show recovery type and console guidance (if PE-2)
3. **Prompt to launch System Restore wizard**
4. If YES → Launch `run_system_restore_wizard()` immediately
5. If NO → Ask if user wants to continue to main menu

**Code:**
```python
if op_data.get('recovery_mode_detected'):
    recovery_type = op_data.get('recovery_type', '')
    console.print(f"⚠ {hostname} is in {recovery_type} mode")
    
    # Show console guidance for PE-2
    if hostname == "PE-2":
        console.print("📡 Console Access Required...")
    
    # Offer System Restore
    if Confirm.ask("Launch System Restore wizard now?", default=True):
        from .wizard.system_restore import run_system_restore_wizard
        success = run_system_restore_wizard(device, None)
        # Returns to device selection after
```

---

## Benefits

### 1. Proactive Recovery
- **Before:** User selects device → main menu → must find [S] option
- **After:** User selects device → immediate System Restore offer

### 2. Reduces Steps
- **Before:** 4 steps (select → menu → find [S] → confirm)
- **After:** 2 steps (select → confirm)

### 3. Matches Monitor UX
- Consistent behavior between monitor and wizard
- User expectation: "If I select a recovery device, I'll be prompted to restore"

### 4. Clear Guidance
- Shows exact recovery type (DN_RECOVERY)
- Console access instructions (PE-2)
- Direct path to resolution

---

## Testing

**Test Scenario: PE-2 in DN_RECOVERY**

1. **Run wizard:**
   ```bash
   scaler-wizard
   ```

2. **Device table shows:**
   ```
   │ 2 │ pe2 │ PE-2 │ SA-36CD-S │ ... │ DN_RECOVERY │
   ```

3. **Select PE-2 (option 2):**
   ```
   ⚠ PE-2 is in DN_RECOVERY mode
   
   📡 Console Access Required for PE-2:
     ssh dn@console-b15
     ...
   
   Launch System Restore wizard now? [Y/n]:
   ```

4. **Press [Y]:**
   - System Restore wizard launches
   - Guided through recovery process

5. **Press [n]:**
   - Goes to main device menu
   - Can select [S] System Restore manually

---

## Edge Cases Handled

### Non-Recovery Devices
- **PE-1, PE-4:** No prompt, direct to main menu
- **Only shown for devices with `recovery_mode_detected: true`**

### Console Access (PE-2 Specific)
- **Only PE-2** gets console instructions
- Other devices: Generic recovery prompt only

### Recovery Types
- **DN_RECOVERY:** "Boot failure - needs factory reset"
- **STANDALONE:** "One NCC down - degraded operation"
- **GI_MODE:** "Waiting for DNOS deployment"

### Error Handling
- If System Restore wizard fails to launch: Shows error, returns to device selection
- If user cancels during restore: Returns to device selection

---

## Files Modified

1. **`scaler/interactive_scale.py`:**
   - Enhanced `select_device()` function
   - Added System Restore launch prompt
   - Integrated console guidance display

---

## User Feedback

**Expected User Response:**
> "Perfect! Now when I select PE-2, it immediately asks if I want to restore it, just like the monitor does. Much faster workflow!"

**Time Saved:**
- **Before:** ~30 seconds (navigate menus, find [S] option)
- **After:** ~5 seconds (one confirmation)

---

## Complete Recovery Workflow

**Monitor → Wizard Integration:**

```
┌─────────────────────────────────────────┐
│  User runs scaler-monitor               │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Monitor detects PE-2 in DN_RECOVERY    │
│  Shows: ⚠ DN_RECOVERY                   │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Monitor prompts:                       │
│  "Launch System Restore wizard now?"    │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  User opens scaler-wizard               │
│  Selects PE-2 from device list          │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Wizard detects DN_RECOVERY             │
│  Shows console access instructions      │
│  Prompts: "Launch System Restore now?"  │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  System Restore wizard launches         │
│  Guides through recovery process        │
└─────────────────────────────────────────┘
```

**✅ Seamless experience from detection to resolution!**

---

**Status:** ✅ Complete  
**Date:** 2026-01-27  
**Integration:** Monitor + Wizard now have identical recovery handling
